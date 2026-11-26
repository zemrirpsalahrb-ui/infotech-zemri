from . import noest_client
import base64
import os
import uuid
from decimal import Decimal, InvalidOperation
from datetime import timedelta
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    CustomerProfile,
    Category,
    Brand,
    Product,
    ProductImage,
    Banner,
    Review,
    OnlineOrder,
    OnlineOrderItem,
    SyncLog,
    DesktopStoreSnapshot,
)
from .permissions import IsAdminOrStaff, HasDesktopApiKey
from .serializers import (
    get_request_tier,
    CustomerProfileSerializer,
    CategorySerializer,
    BrandSerializer,
    ProductSerializer,
    AdminProductWriteSerializer,
    ProductImageSerializer,
    BannerSerializer,
    ReviewSerializer,
    OnlineOrderSerializer,
    SyncLogSerializer,
    DesktopStoreSnapshotSerializer,
)


def to_dec(val, default="0.00") -> Decimal:
    if val is None or val == "":
        return Decimal(default)
    try:
        s = str(val).strip().replace(",", ".").replace(" ", "")
        return Decimal(s).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def infer_category_and_kit_meta(name: str, ref: str):
    """Automatically maps a desktop product name to a CCTV category and Kit Builder role."""
    u = f"{name} {ref}".upper()
    if any(k in u for k in ("NVR", "POE")):
        ch = 16 if "16" in u else (8 if "8" in u else (32 if "32" in u else 4))
        return "NVR", "RECORDER", "IP", ch
    if any(k in u for k in ("XVR", "DVR")):
        ch = 16 if "16" in u else (8 if "8" in u else (32 if "32" in u else 4))
        return "DVR", "RECORDER", "ANALOG_HD", ch
    if any(k in u for k in ("DISQUE", "HDD", "PURPLE", "PERPEL", "SKYHAWK", "500 GB", "1 TB", "2 TB", "4 TB", "6 TB")):
        return "Surveillance Hard Drives", "HDD", "ALL", 0
    if any(k in u for k in ("ALIMENTATION", "BLOC", "CHARGEUR", "12V", "PSU")):
        return "Power Supplies", "PSU", "ALL", 0
    if any(k in u for k in ("BNC", "BALUN", "CONNECTEUR", "FICHE", "RJ45")):
        return "Connectors", "CONNECTOR", "ALL", 0
    if any(k in u for k in ("CABLE", "COAXIAL", "RG59", "CAT6", "CAT5", "HDMI", "VGA", "KVM")):
        return "Cables", "CABLE", "ALL", 0
    if any(k in u for k in ("JONCTION", "BOITE", "SUPPORT", "SPLITER", "SWITCH", "TYPE C", "MODEM", "TAG")):
        return "Accessories", "ACCESSORY", "ALL", 0
    if any(k in u for k in ("ALARME", "SIRENE", "DETECTEUR")):
        return "Alarm Systems", "ACCESSORY", "ALL", 0
    if any(k in u for k in ("KIT COMPLET", "PACK CCTV", "KIT 4", "KIT 8")):
        return "Complete CCTV Kits", "COMPLETE_KIT", "ALL", 0
    if any(k in u for k in ("PTZ", "SPEED DOME", "360")):
        return "PTZ Cameras", "CAMERA", "IP", 0
    if any(k in u for k in ("WIFI", "WI-FI", "SMART", "IMOU", "EZVIZ", "C6N", "H8C")):
        return "Wi-Fi Cameras", "CAMERA", "WIFI", 0
    if any(k in u for k in ("IPC", "IP CAM", "POE CAM")):
        return "IP Cameras", "CAMERA", "IP", 0
    return "Analog Cameras", "CAMERA", "ANALOG_HD", 0


def recompute_reservations_and_conflicts():
    """
    Recalculates reserved_stock across all products and flags any open online orders
    that have a stock conflict with the physical stock synced from Desktop.
    """
    now = timezone.now()
    # 1. Expire old reservations
    OnlineOrder.objects.filter(
        reservation_active=True,
        reservation_expires_at__isnull=False,
        reservation_expires_at__lt=now,
    ).update(reservation_active=False)

    # 2. Recompute reserved_stock per product for active unconverted reservations
    reserved_map = {}
    active_orders = OnlineOrder.objects.filter(
        reservation_active=True,
        pos_converted=False,
        status__in=["CONFIRMED", "PREPARING", "READY_FOR_PICKUP"],
    ).prefetch_related("items")

    for order in active_orders:
        for item in order.items.all():
            if item.product_id:
                reserved_map[item.product_id] = reserved_map.get(item.product_id, Decimal("0.00")) + item.quantity

    for prod in Product.objects.all():
        new_res = reserved_map.get(prod.id, Decimal("0.00"))
        if prod.reserved_stock != new_res:
            prod.reserved_stock = new_res
            prod.save(update_fields=["reserved_stock"])

    # 3. Check all open unconverted orders for conflicts against physical_stock
    open_orders = OnlineOrder.objects.filter(
        pos_converted=False,
        status__in=["NEW", "PENDING", "CONFIRMED", "PREPARING", "READY_FOR_PICKUP"],
    ).prefetch_related("items__product")

    conflicts_found = []
    for order in open_orders:
        order_conflicts = []
        for item in order.items.all():
            p = item.product
            if not p:
                p = Product.objects.filter(reference=item.product_reference).first()
            if p:
                other_reserved = max(
                    Decimal("0.00"),
                    p.reserved_stock - (item.quantity if order.reservation_active else Decimal("0.00")),
                )
                effective_avail = p.physical_stock - other_reserved
                if item.quantity > effective_avail:
                    msg = (
                        f"{p.name} ({p.reference}): demandé {item.quantity}, "
                        f"stock physique {p.physical_stock}, réservé {other_reserved}"
                    )
                    order_conflicts.append(msg)
        has_conflict = len(order_conflicts) > 0
        details_str = " | ".join(order_conflicts)
        if order.has_stock_conflict != has_conflict or order.conflict_details != details_str:
            order.has_stock_conflict = has_conflict
            order.conflict_details = details_str
            order.save(update_fields=["has_stock_conflict", "conflict_details"])
        if has_conflict:
            conflicts_found.append({"order_uid": order.order_uid, "details": details_str})
    return conflicts_found


# ============================================================================
# 1. PUBLIC & CATALOG ENDPOINTS
# ============================================================================

class HomeCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ctx = {"request": request}
        qs = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images", "reviews")
        featured = qs.filter(is_featured=True)[:8]
        if not featured:
            featured = qs[:8]
        bestsellers = qs.filter(is_bestseller=True)[:8]
        if not bestsellers:
            bestsellers = qs[4:12]
        new_arrivals = qs.filter(is_new_arrival=True)[:8]
        if not new_arrivals:
            new_arrivals = qs.order_by("-id")[:8]
        special_offers = qs.filter(Q(is_special_offer=True) | Q(promo_price__isnull=False))[:8]

        categories = Category.objects.filter(is_active=True).annotate(
            product_count=Count("products", filter=Q(products__is_active=True))
        )
        brands = Brand.objects.annotate(
            product_count=Count("products", filter=Q(products__is_active=True))
        )
        banners = Banner.objects.filter(is_active=True)

        return Response({
            "business_name": settings.BUSINESS_NAME,
            "whatsapp": settings.BUSINESS_WHATSAPP,
            "applied_tier": get_request_tier(request),
            "banners": BannerSerializer(banners, many=True).data,
            "categories": CategorySerializer(categories, many=True).data,
            "brands": BrandSerializer(brands, many=True).data,
            "featured_products": ProductSerializer(featured, many=True, context=ctx).data,
            "bestsellers": ProductSerializer(bestsellers, many=True, context=ctx).data,
            "new_arrivals": ProductSerializer(new_arrivals, many=True, context=ctx).data,
            "special_offers": ProductSerializer(special_offers, many=True, context=ctx).data,
        })


class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images", "reviews")

        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(reference__icontains=q)
                | Q(brand_raw__icontains=q)
                | Q(short_description__icontains=q)
                | Q(description__icontains=q)
            )

        category = request.query_params.get("category", "").strip()
        if category and category != "all":
            if category.isdigit():
                qs = qs.filter(category_id=int(category))
            else:
                qs = qs.filter(category__slug=category)

        brand = request.query_params.get("brand", "").strip()
        if brand and brand != "all":
            if brand.isdigit():
                qs = qs.filter(brand_id=int(brand))
            else:
                qs = qs.filter(Q(brand__slug=brand) | Q(brand_raw__iexact=brand))

        kit_type = request.query_params.get("kit_type", "").strip()
        if kit_type:
            qs = qs.filter(kit_component_type=kit_type)

        kit_tech = request.query_params.get("kit_tech", "").strip()
        if kit_tech and kit_tech != "ALL":
            qs = qs.filter(Q(kit_technology=kit_tech) | Q(kit_technology="ALL"))

        min_price = request.query_params.get("min_price", "").strip()
        if min_price:
            qs = qs.filter(public_price__gte=to_dec(min_price))

        max_price = request.query_params.get("max_price", "").strip()
        if max_price:
            qs = qs.filter(public_price__lte=to_dec(max_price))

        in_stock = request.query_params.get("in_stock", "").strip().lower()
        if in_stock in ("true", "1", "yes"):
            qs = [p for p in qs if p.available_stock > 0]
        else:
            qs = list(qs)

        sort_by = request.query_params.get("sort", "").strip()
        tier = get_request_tier(request)
        if sort_by == "price_asc":
            qs.sort(key=lambda p: p.get_unit_price_for_tier(tier))
        elif sort_by == "price_desc":
            qs.sort(key=lambda p: p.get_unit_price_for_tier(tier), reverse=True)
        elif sort_by == "newest":
            qs.sort(key=lambda p: p.id, reverse=True)
        elif sort_by == "name":
            qs.sort(key=lambda p: p.name.lower())

        limit = int(request.query_params.get("limit", "100"))
        ctx = {"request": request}
        return Response({
            "count": len(qs),
            "applied_tier": tier,
            "results": ProductSerializer(qs[:limit], many=True, context=ctx).data,
        })


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, lookup):
        qs = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images", "reviews")
        product = qs.filter(Q(slug=lookup) | Q(reference__iexact=lookup)).first()
        if not product and str(lookup).isdigit():
            product = qs.filter(id=int(lookup)).first()
        if not product:
            return Response({"error": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)

        related = Product.objects.filter(is_active=True).exclude(id=product.id)
        if product.category_id:
            related = related.filter(category_id=product.category_id)
        related = related.select_related("category", "brand").prefetch_related("images")[:4]

        ctx = {"request": request, "include_reviews": True}
        return Response({
            "product": ProductSerializer(product, context=ctx).data,
            "related_products": ProductSerializer(related, many=True, context={"request": request}).data,
        })


class ProductReviewCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response({"error": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)

        rating = int(request.data.get("rating", 5))
        if rating < 1 or rating > 5:
            return Response({"error": "La note doit être comprise entre 1 et 5 étoiles."}, status=status.HTTP_400_BAD_REQUEST)

        comment = str(request.data.get("comment", "")).strip()
        if len(comment) < 5:
            return Response({"error": "Veuillez écrire un commentaire d'au moins 5 caractères."}, status=status.HTTP_400_BAD_REQUEST)

        author_name = str(request.data.get("author_name", "")).strip()
        user = request.user if request.user.is_authenticated else None
        if user and not author_name:
            author_name = user.get_full_name() or user.username
        if not author_name:
            author_name = "Client Visiteur"

        # Check verified purchase badge: only True when the customer actually purchased & received the product
        verified = False
        if user:
            verified = OnlineOrderItem.objects.filter(
                order__user=user,
                order__status__in=["CONFIRMED", "DELIVERED"],
                product=product,
            ).exists()
        else:
            phone = str(request.data.get("phone", "")).strip()
            if phone:
                verified = OnlineOrderItem.objects.filter(
                    order__customer_phone=phone,
                    order__status__in=["CONFIRMED", "DELIVERED"],
                    product=product,
                ).exists()

        review = Review.objects.create(
            product=product,
            user=user,
            author_name=author_name[:120],
            rating=rating,
            title=str(request.data.get("title", "")).strip()[:180],
            comment=comment[:2000],
            is_verified_purchase=verified,
            status="PENDING",
        )
        return Response({
            "message": "Merci ! Votre avis a été soumis et sera publié après validation par l'administrateur.",
            "review": ReviewSerializer(review).data,
        }, status=status.HTTP_201_CREATED)


# ============================================================================
# 2. ADVANCED CCTV KIT BUILDER
# ============================================================================

class KitBuilderEvaluateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Returns grouped products for each step of the CCTV Kit Builder."""
        ctx = {"request": request}
        qs = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images")
        return Response({
            "applied_tier": get_request_tier(request),
            "cameras": ProductSerializer(qs.filter(kit_component_type="CAMERA"), many=True, context=ctx).data,
            "recorders": ProductSerializer(qs.filter(kit_component_type="RECORDER"), many=True, context=ctx).data,
            "hdds": ProductSerializer(qs.filter(kit_component_type="HDD"), many=True, context=ctx).data,
            "psus": ProductSerializer(qs.filter(kit_component_type="PSU"), many=True, context=ctx).data,
            "cables": ProductSerializer(qs.filter(kit_component_type="CABLE"), many=True, context=ctx).data,
            "connectors": ProductSerializer(qs.filter(kit_component_type="CONNECTOR"), many=True, context=ctx).data,
            "accessories": ProductSerializer(qs.filter(kit_component_type="ACCESSORY"), many=True, context=ctx).data,
        })

    def post(self, request):
        """
        Validates compatibility of a custom CCTV package and calculates authoritative package pricing.
        Expected payload: { "items": [{"product_id": 1, "quantity": 4}, ...] }
        """
        tier = get_request_tier(request)
        raw_items = request.data.get("items", [])
        detailed_items = []
        total_cameras = 0
        camera_techs = set()
        recorder_channels = 0
        recorder_techs = set()
        has_hdd = False
        has_psu = False
        has_connectors = False
        package_subtotal = Decimal("0.00")

        for entry in raw_items:
            pid = entry.get("product_id")
            qty = int(float(entry.get("quantity", 1)))
            if not pid or qty <= 0:
                continue
            prod = Product.objects.filter(id=pid, is_active=True).first()
            if not prod:
                continue
            unit_price = prod.get_unit_price_for_tier(tier)
            line_total = unit_price * Decimal(qty)
            package_subtotal += line_total

            if prod.kit_component_type == "CAMERA":
                total_cameras += qty
                if prod.kit_technology != "ALL":
                    camera_techs.add(prod.kit_technology)
            elif prod.kit_component_type == "RECORDER":
                recorder_channels += (prod.kit_channels or 8) * qty
                if prod.kit_technology != "ALL":
                    recorder_techs.add(prod.kit_technology)
            elif prod.kit_component_type == "HDD":
                has_hdd = True
            elif prod.kit_component_type == "PSU":
                has_psu = True
            elif prod.kit_component_type == "CONNECTOR":
                has_connectors = True

            detailed_items.append({
                "product_id": prod.id,
                "reference": prod.reference,
                "name": prod.name,
                "component_type": prod.kit_component_type,
                "quantity": qty,
                "unit_price": float(unit_price),
                "line_total": float(line_total),
                "in_stock": prod.available_stock >= qty,
            })

        warnings = []
        recommendations = []
        is_compatible = True

        if total_cameras > 0 and recorder_channels > 0 and total_cameras > recorder_channels:
            is_compatible = False
            warnings.append(
                f"Capacité dépassée : vous avez sélectionné {total_cameras} caméras pour un enregistreur de {recorder_channels} canaux maximum."
            )
            recommendations.append("Optez pour un XVR/NVR de 8 ou 16 canaux.")

        if "IP" in camera_techs and "ANALOG_HD" in recorder_techs and "IP" not in recorder_techs:
            warnings.append("Attention : vérifiez le mode hybride IP sur le XVR pour supporter toutes les caméras IP.")

        if total_cameras > 0 and recorder_channels == 0:
            recommendations.append("Ajoutez un enregistreur DVR / XVR / NVR pour enregistrer vos caméras 24h/24.")
        if total_cameras > 0 and not has_hdd:
            recommendations.append(
                f"Recommandé : Ajoutez un Disque Dur Surveillance (ex: {max(1, (total_cameras + 3) // 4)} TB Purple) pour ~15 à 30 jours d'enregistrement."
            )
        if total_cameras > 0 and not has_psu and "IP" not in camera_techs:
            recommendations.append(
                f"Recommandé : Ajoutez un Bloc d'alimentation 12V ({max(4, total_cameras)} sorties) ou {total_cameras} chargeurs 12V 2A."
            )
        if total_cameras > 0 and not has_connectors and "ANALOG_HD" in camera_techs:
            recommendations.append(
                f"Recommandé : Ajoutez {total_cameras * 2} fiches BNC et {total_cameras} fiches d'alimentation."
            )

        return Response({
            "applied_tier": tier,
            "is_compatible": is_compatible,
            "total_cameras": total_cameras,
            "recorder_channels": recorder_channels,
            "package_total": float(package_subtotal),
            "items": detailed_items,
            "warnings": warnings,
            "recommendations": recommendations,
        })


# ============================================================================
# 3. AUTHENTICATION & CUSTOMER ACCOUNTS (PUBLIC / INSTALLER / RESELLER)
# ============================================================================

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        email = str(request.data.get("email", "")).strip()
        password = str(request.data.get("password", "")).strip()
        first_name = str(request.data.get("first_name", "")).strip()
        last_name = str(request.data.get("last_name", "")).strip()
        requested_role = str(request.data.get("account_type", "PUBLIC")).strip().upper()

        if not username or not password:
            return Response({"error": "Nom d'utilisateur et mot de passe obligatoires."}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 6:
            return Response({"error": "Le mot de passe doit contenir au moins 6 caractères."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username__iexact=username).exists():
            return Response({"error": "Ce nom d'utilisateur est déjà utilisé."}, status=status.HTTP_400_BAD_REQUEST)

        if requested_role not in ("PUBLIC", "INSTALLER", "RESELLER"):
            requested_role = "PUBLIC"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Installers & Resellers remain PENDING until administrator approval and see PUBLIC prices meanwhile
        approval_status = "PENDING" if requested_role in ("INSTALLER", "RESELLER") else "NONE"
        profile = CustomerProfile.objects.create(
            user=user,
            account_type=requested_role,
            requested_type=requested_role,
            approval_status=approval_status,
            phone=str(request.data.get("phone", "")).strip(),
            company_name=str(request.data.get("company_name", "")).strip(),
            wilaya=str(request.data.get("wilaya", "")).strip(),
            address=str(request.data.get("address", "")).strip(),
            rc_number=str(request.data.get("rc_number", "")).strip(),
            nif_number=str(request.data.get("nif_number", "")).strip(),
            professional_justification=str(request.data.get("professional_justification", "")).strip(),
        )

        refresh = RefreshToken.for_user(user)
        msg = "Compte créé avec succès."
        if approval_status == "PENDING":
            msg = (
                f"Votre demande de compte professionnel ({requested_role}) a bien été enregistrée. "
                "Votre compte est en attente de validation par l'administrateur. En attendant, vous bénéficiez des tarifs publics."
            )

        return Response({
            "message": msg,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "profile": CustomerProfileSerializer(profile).data,
        }, status=status.HTTP_201_CREATED)


class LoginRateThrottle(AnonRateThrottle):
    """Anti brute-force : 8 tentatives de connexion par minute et par adresse IP."""
    scope = "login"
    rate = "8/min"


DEFAULT_OWNER_CODES = ("admin123", "pro12345", "gros12345")


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", "")).strip()
        user = authenticate(request, username=username, password=password)
        if not user:
            # Allow login by email as well
            u_by_email = User.objects.filter(email__iexact=username).first()
            if u_by_email:
                user = authenticate(request, username=u_by_email.username, password=password)

        if not user:
            # Recherche client dans les profils existants
            clean_phone = "".join(c for c in username if c.isdigit())
            prof = None
            if len(clean_phone) >= 8:
                prof = CustomerProfile.objects.filter(phone__icontains=clean_phone).first()
            if not prof:
                prof = CustomerProfile.objects.filter(desktop_client_name__iexact=username).first()
            if not prof and (username.upper().startswith("CL") or username.upper().startswith("CL_")):
                clean_id = "".join(c for c in username if c.isdigit())
                if clean_id:
                    prof = CustomerProfile.objects.filter(desktop_client_id=int(clean_id)).first()

            if prof and prof.user:
                if (prof.desktop_code_web and (prof.desktop_code_web.strip().upper() == password.strip().upper() or prof.desktop_code_web.strip().upper() == username.strip().upper())) or prof.user.check_password(password):
                    user = prof.user

        if not user:
            # Recherche JIT (Just-In-Time) dans le snapshot synchronisé du magasin
            snap = DesktopStoreSnapshot.objects.first()
            if snap and snap.top_debtors:
                u_norm = username.strip().upper()
                p_norm = password.strip().upper()
                clean_phone = "".join(c for c in username if c.isdigit())
                matched_client = None
                for c_item in snap.top_debtors:
                    c_code = str(c_item.get("code_web") or "").strip().upper()
                    c_tel = "".join(c for c in str(c_item.get("tel") or "") if c.isdigit())
                    c_nom = str(c_item.get("nom") or "").strip().upper()
                    c_ide = str(c_item.get("ide") or "")

                    # Correspondance code direct (CLXXXX)
                    if c_code and (u_norm == c_code or p_norm == c_code):
                        matched_client = c_item
                        break
                    # Correspondance par téléphone + code
                    if c_code and clean_phone and len(clean_phone) >= 8 and c_tel and clean_phone in c_tel:
                        if p_norm == c_code or not p_norm:
                            matched_client = c_item
                            break
                    # Correspondance par nom exact + code
                    if c_code and u_norm == c_nom and p_norm == c_code:
                        matched_client = c_item
                        break

                if matched_client:
                    ide = matched_client.get("ide")
                    nom = str(matched_client.get("nom") or "").strip()
                    tel = str(matched_client.get("tel") or "").strip()
                    solde = to_dec(matched_client.get("solde"))
                    code_web = str(matched_client.get("code_web") or "").strip()
                    last_inv = str(matched_client.get("derniere_facture") or "").strip()

                    uname = f"cl_{ide}" if ide else f"cl_{code_web.lower()}"
                    user, _ = User.objects.get_or_create(
                        username=uname,
                        defaults={"first_name": nom[:30], "is_staff": False}
                    )
                    user.set_password(code_web)
                    user.save()

                    prof, _ = CustomerProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            "account_type": "INSTALLER",
                            "requested_type": "INSTALLER",
                            "approval_status": "APPROVED",
                            "desktop_client_name": nom,
                            "desktop_client_id": ide,
                            "desktop_balance": solde,
                            "desktop_code_web": code_web,
                            "last_invoice": last_inv,
                            "phone": tel if (tel and tel != "/") else "",
                        }
                    )
                    prof.account_type = "INSTALLER"
                    prof.requested_type = "INSTALLER"
                    prof.approval_status = "APPROVED"
                    prof.desktop_client_name = nom
                    prof.desktop_client_id = ide
                    prof.desktop_balance = solde
                    prof.desktop_code_web = code_web
                    prof.last_invoice = last_inv
                    if tel and tel != "/":
                        prof.phone = tel
                    prof.save()

        if not user:
            return Response({"error": "Identifiants ou code secret incorrect."}, status=status.HTTP_401_UNAUTHORIZED)

        profile, _ = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "account_type": "ADMIN" if (user.is_staff or user.is_superuser) else "PUBLIC",
                "approval_status": "APPROVED" if (user.is_staff or user.is_superuser) else "NONE",
            },
        )
        if profile.approval_status == "SUSPENDED":
            return Response({"error": "Ce compte a été suspendu par l'administrateur."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        must_change = bool((user.is_staff or user.is_superuser) and any(user.check_password(c) for c in DEFAULT_OWNER_CODES))
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "profile": CustomerProfileSerializer(profile).data,
            "must_change_code": must_change,
        })


class ChangeOwnerCodeView(APIView):
    """Le proprietaire change son code secret (mot de passe) depuis le dashboard."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        current = str(request.data.get("current", ""))
        new = str(request.data.get("new", "")).strip()
        user = request.user
        if not user.check_password(current):
            return Response({"error": "Code actuel incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        if len(new) < 6:
            return Response({"error": "Le nouveau code doit contenir au moins 6 caracteres."}, status=status.HTTP_400_BAD_REQUEST)
        if new in DEFAULT_OWNER_CODES or new == current:
            return Response({"error": "Choisissez un code different et personnel."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new)
        user.save()
        return Response({"ok": True})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        orders = OnlineOrder.objects.filter(user=request.user).prefetch_related("items")[:30]
        return Response({
            "profile": CustomerProfileSerializer(profile).data,
            "orders": OnlineOrderSerializer(orders, many=True).data,
        })


# ============================================================================
# 4. SHOPPING CART CHECKOUT & ORDER TRACKING
# ============================================================================

class CheckoutOrderView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        idempotency_key = (
            request.headers.get("X-Idempotency-Key")
            or request.data.get("idempotency_key")
            or ""
        ).strip()

        if idempotency_key:
            existing = OnlineOrder.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return Response({
                    "message": "Commande déjà enregistrée (idempotence).",
                    "order": OnlineOrderSerializer(existing).data,
                }, status=status.HTTP_200_OK)

        customer_name = str(request.data.get("customer_name", "")).strip()
        customer_phone = str(request.data.get("customer_phone", "")).strip()
        if not customer_name or not customer_phone:
            return Response(
                {"error": "Le nom complet et le numéro de téléphone sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_items = request.data.get("items", [])
        if not raw_items:
            return Response({"error": "Votre panier est vide."}, status=status.HTTP_400_BAD_REQUEST)

        tier = get_request_tier(request)
        delivery_method = str(request.data.get("delivery_method", "DELIVERY")).strip().upper()
        if delivery_method not in ("DELIVERY", "PICKUP"):
            delivery_method = "DELIVERY"

        payment_method = str(request.data.get("payment_method", "CASH_ON_DELIVERY")).strip().upper()
        if payment_method not in ("CASH_ON_DELIVERY", "PAY_AT_STORE", "BANK_TRANSFER", "CIB_EDAHABIA"):
            payment_method = "CASH_ON_DELIVERY"

        date_prefix = timezone.now().strftime("%Y%m%d")
        rand_suffix = uuid.uuid4().hex[:5].upper()
        order_uid = f"WEB-{date_prefix}-{rand_suffix}"

        # NOEST delivery fields
        raw_wilaya = str(request.data.get("wilaya", "Oran")).strip()
        wilaya_id = request.data.get("wilaya_id")
        delivery_commune = str(request.data.get("commune", "")).strip()
        delivery_type = str(request.data.get("delivery_type", "")).strip().upper()
        delivery_stop_desk = bool(request.data.get("stop_desk", False) or delivery_type == "STOPDESK")
        delivery_station_code = str(request.data.get("station_code", "")).strip()

        # Calcul automatique des frais de livraison NOEST
        shipping_fee = Decimal("0.00")
        if delivery_method == "DELIVERY":
            try:
                fees_data = noest_client.get_fees().get("tarifs", {}).get("delivery", {})
                w_key = str(wilaya_id) if wilaya_id else "31"
                w_tarifs = fees_data.get(w_key, {})
                if delivery_stop_desk:
                    shipping_fee = Decimal(str(w_tarifs.get("tarif_stopdesk", "250.00")))
                else:
                    shipping_fee = Decimal(str(w_tarifs.get("tarif", "500.00")))
            except Exception:
                shipping_fee = to_dec(request.data.get("shipping_fee", "600.00"), "600.00")

        order = OnlineOrder.objects.create(
            order_uid=order_uid,
            idempotency_key=idempotency_key or None,
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=str(request.data.get("customer_email", "")).strip(),
            company_name=str(request.data.get("company_name", "")).strip(),
            wilaya=raw_wilaya,
            delivery_address=str(request.data.get("delivery_address", "")).strip(),
            delivery_commune=delivery_commune,
            delivery_stop_desk=delivery_stop_desk,
            delivery_station_code=delivery_station_code,
            notes=str(request.data.get("notes", "")).strip(),
            applied_tier=tier,
            delivery_method=delivery_method,
            payment_method=payment_method,
            status="NEW",
            shipping_fee=shipping_fee,
        )

        subtotal = Decimal("0.00")
        conflicts = []

        for entry in raw_items:
            pid = entry.get("product_id")
            ref = str(entry.get("reference", "")).strip()
            qty = to_dec(entry.get("quantity", 1), "1.00")
            if qty <= Decimal("0.00"):
                continue

            product = None
            if pid:
                product = Product.objects.select_for_update().filter(id=pid).first()
            if not product and ref:
                product = Product.objects.select_for_update().filter(reference__iexact=ref).first()
            if not product:
                raise ValueError(f"Produit introuvable ({ref or pid}).")

            # CRITICAL SECURITY RULE: Never trust a price submitted by the frontend!
            unit_price = product.get_unit_price_for_tier(tier)
            line_total = (unit_price * qty).quantize(Decimal("0.01"))
            subtotal += line_total

            if qty > product.available_stock:
                conflicts.append(
                    f"{product.name} ({product.reference}): commandé {qty}, disponible {product.available_stock}"
                )

            OnlineOrderItem.objects.create(
                order=order,
                product=product,
                desktop_ide=product.desktop_ide,
                product_reference=product.reference,
                product_name=product.name,
                quantity=qty,
                applied_unit_price=unit_price,
                public_unit_price_snapshot=product.public_price,
                line_total=line_total,
            )

        if delivery_method == "PICKUP":
            shipping_fee = Decimal("0.00")
        elif subtotal > Decimal("100000.00"):
            # Règle commerciale : si la valeur totale des produits dépasse 100 000 DA, les frais de livraison sont doublés
            shipping_fee = (shipping_fee * Decimal("2.00")).quantize(Decimal("0.01"))

        order.subtotal = subtotal
        order.shipping_fee = shipping_fee
        order.total_amount = subtotal + shipping_fee
        if conflicts:
            order.has_stock_conflict = True
            order.conflict_details = " | ".join(conflicts)
        order.save()

        # Envoi automatique vers NOEST Livraison
        if delivery_method == "DELIVERY" and getattr(settings, "NOEST_AUTO_CREATE", True):
            try:
                noest_res = noest_client.create_noest_order(
                    order=order,
                    wilaya_id=wilaya_id,
                    commune_name=delivery_commune,
                    stop_desk=1 if delivery_stop_desk else 0,
                    station_code=delivery_station_code
                )
                if noest_res.get("success"):
                    tracking = noest_res.get("tracking", "")
                    order.delivery_tracking = tracking
                    order.delivery_status = "SENT_TO_NOEST"
                    order.delivery_label_url = f"https://app.noest-dz.com/api/public/get/order/label?tracking={tracking}"
                    order.save(update_fields=["delivery_tracking", "delivery_status", "delivery_label_url"])
                    if getattr(settings, "NOEST_AUTO_VALIDATE", False) and tracking:
                        noest_client.validate_noest_order(tracking)
                else:
                    order.delivery_error = str(noest_res.get("error", ""))
                    order.save(update_fields=["delivery_error"])
            except Exception as e:
                order.delivery_error = str(e)
                order.save(update_fields=["delivery_error"])

        return Response({
            "message": "Votre commande a été enregistrée avec succès !",
            "order": OnlineOrderSerializer(order).data,
            "delivery_tracking": order.delivery_tracking,
            "delivery_status": order.delivery_status,
            "whatsapp_number": settings.BUSINESS_WHATSAPP,
        }, status=status.HTTP_201_CREATED)


class OrderTrackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, order_uid):
        order = OnlineOrder.objects.prefetch_related("items").filter(order_uid__iexact=order_uid.strip()).first()
        if not order:
            return Response({"error": "Aucune commande trouvée avec ce numéro."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"order": OnlineOrderSerializer(order).data})


# ============================================================================
# 5. DESKTOP APPLICATION SYNCHRONIZATION ENDPOINTS (OUTBOUND FROM JAVA SWING)
# ============================================================================

class DesktopSyncProductsView(APIView):
    """
    Receives outbound product/price/stock synchronization from the local Java Swing software.
    Desktop is the primary source of truth for references, core prices, and physical stock.
    Website-enriched descriptions, specs, and images in Neon are preserved!
    """
    permission_classes = [HasDesktopApiKey]

    @transaction.atomic
    def post(self, request):
        idempotency_key = (
            request.headers.get("X-Idempotency-Key")
            or request.data.get("idempotency_key")
            or ""
        ).strip()

        if idempotency_key and SyncLog.objects.filter(idempotency_key=idempotency_key, status="SUCCESS").exists():
            return Response({
                "status": "ALREADY_PROCESSED",
                "idempotency_key": idempotency_key,
                "conflicts": recompute_reservations_and_conflicts(),
            })

        products_data = request.data.get("products", [])
        created_count = 0
        updated_count = 0
        now = timezone.now()

        # Pre-cache categories & brands
        cat_cache = {c.name.upper(): c for c in Category.objects.all()}
        brand_cache = {b.name.upper(): b for b in Brand.objects.all()}

        for item in products_data:
            ref = str(item.get("reference", "")).strip()
            ide = item.get("ide")
            name = str(item.get("nom") or item.get("name") or "").strip()
            if not name and not ref:
                continue
            if not ref:
                ref = f"P{int(ide):06d}" if ide else f"P-{uuid.uuid4().hex[:6].upper()}"

            prix_vente = to_dec(item.get("prix_vente"), "0.00")
            prix_gros = to_dec(item.get("prix_gros"), "0.00")
            if prix_gros <= Decimal("0.00") or prix_gros > prix_vente:
                prix_gros = prix_vente
            qte = to_dec(item.get("qte"), "0.00")
            tva = to_dec(item.get("tva"), "19.00")
            marque = str(item.get("marque", "")).strip()

            cat_name, kit_comp, kit_tech, kit_ch = infer_category_and_kit_meta(name, ref)
            cat_obj = cat_cache.get(cat_name.upper())
            if not cat_obj:
                cat_obj, _ = Category.objects.get_or_create(name=cat_name)
                cat_cache[cat_name.upper()] = cat_obj

            brand_obj = None
            if marque and marque.upper() not in ("B", "NULL", "/", "-"):
                brand_obj = brand_cache.get(marque.upper())
                if not brand_obj:
                    brand_obj, _ = Brand.objects.get_or_create(name=marque.upper())
                    brand_cache[marque.upper()] = brand_obj

            prod = None
            if ide:
                prod = Product.objects.filter(desktop_ide=int(ide)).first()
            if not prod:
                prod = Product.objects.filter(reference__iexact=ref).first()

            if prod:
                prod.desktop_ide = int(ide) if ide else prod.desktop_ide
                prod.reference = ref
                prod.name = name or prod.name
                prod.brand_raw = marque
                if brand_obj and not prod.brand_id:
                    prod.brand = brand_obj
                if not prod.category_id:
                    prod.category = cat_obj
                if prod.kit_component_type == "NONE":
                    prod.kit_component_type = kit_comp
                    prod.kit_technology = kit_tech
                    prod.kit_channels = kit_ch
                prod.public_price = prix_vente
                prod.reseller_price = prix_gros
                # Update installer_price proportionally if not custom overridden
                if prod.installer_price <= Decimal("0.00") or prod.installer_price > prix_vente:
                    prod.installer_price = prix_gros if prix_gros < prix_vente else prix_vente
                prod.physical_stock = qte
                prod.tva_rate = tva if tva > Decimal("0.00") else Decimal("19.00")
                prod.last_desktop_sync = now
                prod.save()
                updated_count += 1
            else:
                installer_p = prix_gros if prix_gros < prix_vente else prix_vente
                Product.objects.create(
                    desktop_ide=int(ide) if ide else None,
                    reference=ref,
                    name=name,
                    category=cat_obj,
                    brand=brand_obj,
                    brand_raw=marque,
                    public_price=prix_vente,
                    installer_price=installer_p,
                    reseller_price=prix_gros,
                    physical_stock=qte,
                    tva_rate=tva if tva > Decimal("0.00") else Decimal("19.00"),
                    kit_component_type=kit_comp,
                    kit_technology=kit_tech,
                    kit_channels=kit_ch,
                    short_description=f"Équipement professionnel {name} (Réf: {ref}).",
                    warranty_months=0,
                    last_desktop_sync=now,
                )
                created_count += 1

        conflicts = recompute_reservations_and_conflicts()
        SyncLog.objects.create(
            idempotency_key=idempotency_key or None,
            direction="DESKTOP_TO_WEB",
            event_type="STOCK_PUSH",
            status="CONFLICT" if conflicts else "SUCCESS",
            summary=f"Sync Desktop: {created_count} créés, {updated_count} mis à jour, {len(conflicts)} conflits.",
            details=str(conflicts[:10]) if conflicts else "",
        )

        return Response({
            "status": "OK",
            "created": created_count,
            "updated": updated_count,
            "conflicts": conflicts,
            "timestamp": now.isoformat(),
        })


class DesktopOrdersListView(APIView):
    """Returns online orders to the Java Swing ONLINE ORDERS module."""
    permission_classes = [HasDesktopApiKey]

    def get(self, request):
        recompute_reservations_and_conflicts()
        qs = OnlineOrder.objects.prefetch_related("items").all()
        status_filter = request.query_params.get("status", "").strip().upper()
        if status_filter and status_filter != "ALL":
            qs = qs.filter(status=status_filter)
        unconverted = request.query_params.get("unconverted_only", "").strip().lower()
        if unconverted in ("true", "1", "yes"):
            qs = qs.filter(pos_converted=False)
        limit = int(request.query_params.get("limit", "200"))
        return Response({
            "count": qs.count(),
            "orders": OnlineOrderSerializer(qs[:limit], many=True).data,
        })


class DesktopOrderStatusUpdateView(APIView):
    """
    Allows the Desktop application (or Website Admin) to update an OnlineOrder status
    and manages stock reservations automatically.
    """
    permission_classes = [HasDesktopApiKey]

    @transaction.atomic
    def post(self, request, order_uid):
        order = OnlineOrder.objects.select_for_update().prefetch_related("items").filter(order_uid=order_uid).first()
        if not order:
            return Response({"error": "Commande introuvable."}, status=status.HTTP_404_NOT_FOUND)

        new_status = str(request.data.get("status", "")).strip().upper()
        valid_statuses = {c[0] for c in OnlineOrder.STATUS_CHOICES}
        if new_status not in valid_statuses:
            return Response({"error": f"Statut invalide: {new_status}"}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = new_status

        # Activate stock reservation when order is confirmed/preparing/ready and not yet POS-converted
        if new_status in ("CONFIRMED", "PREPARING", "READY_FOR_PICKUP") and not order.pos_converted:
            order.reservation_active = True
            order.reservation_expires_at = timezone.now() + timedelta(hours=settings.RESERVATION_EXPIRY_HOURS)
        elif new_status in ("CANCELLED", "REJECTED", "DELIVERED", "SHIPPED"):
            if new_status in ("CANCELLED", "REJECTED"):
                order.reservation_active = False
                order.reservation_expires_at = None

        order.save()
        conflicts = recompute_reservations_and_conflicts()
        order.refresh_from_db()

        SyncLog.objects.create(
            direction="DESKTOP_TO_WEB",
            event_type="ORDER_STATUS",
            status="CONFLICT" if order.has_stock_conflict else "SUCCESS",
            summary=f"Commande {order.order_uid}: {old_status} -> {new_status}",
            details=order.conflict_details,
        )

        return Response({
            "message": f"Statut de la commande {order.order_uid} mis à jour : {new_status}",
            "order": OnlineOrderSerializer(order).data,
            "conflicts": conflicts,
        })


class DesktopOrderConvertPosView(APIView):
    """
    Records that an OnlineOrder has been converted into an official POS sale in the Java Swing application.
    Guarantees idempotency so an online order is NEVER converted twice or deducted twice!
    """
    permission_classes = [HasDesktopApiKey]

    @transaction.atomic
    def post(self, request, order_uid):
        order = OnlineOrder.objects.select_for_update().prefetch_related("items__product").filter(order_uid=order_uid).first()
        if not order:
            return Response({"error": "Commande en ligne introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if order.pos_converted:
            return Response({
                "already_converted": True,
                "message": f"Cette commande a déjà été convertie en Bon N° {order.pos_bon_number}.",
                "order": OnlineOrderSerializer(order).data,
            }, status=status.HTTP_200_OK)

        bon_number = str(request.data.get("pos_bon_number", "")).strip()
        caissier = str(request.data.get("caissier", "admin")).strip()
        new_status = str(request.data.get("status", "CONFIRMED")).strip().upper()
        if not bon_number:
            return Response({"error": "Numéro de bon POS requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Update synced physical stocks if provided by desktop after VenteService.valider
        updated_stocks = request.data.get("updated_stocks", [])
        for st_entry in updated_stocks:
            ref = str(st_entry.get("reference", "")).strip()
            new_qte = to_dec(st_entry.get("qte"), "0.00")
            if ref:
                Product.objects.filter(reference__iexact=ref).update(
                    physical_stock=new_qte,
                    last_desktop_sync=timezone.now(),
                )

        order.pos_converted = True
        order.pos_bon_number = bon_number
        order.pos_converted_at = timezone.now()
        order.pos_converted_by = caissier
        order.reservation_active = False  # Physical stock has now been deducted in POS!
        order.has_stock_conflict = False
        order.conflict_details = ""
        if order.status in ("NEW", "PENDING"):
            order.status = new_status if new_status in ("CONFIRMED", "PREPARING", "READY_FOR_PICKUP", "DELIVERED") else "CONFIRMED"
        order.save()

        recompute_reservations_and_conflicts()

        SyncLog.objects.create(
            idempotency_key=f"POS-CONV-{order.order_uid}",
            direction="DESKTOP_TO_WEB",
            event_type="POS_CONVERSION",
            status="SUCCESS",
            summary=f"Commande {order.order_uid} convertie en Bon POS N° {bon_number} par {caissier}",
        )

        return Response({
            "already_converted": False,
            "message": f"Commande {order.order_uid} liée au Bon POS N° {bon_number}.",
            "order": OnlineOrderSerializer(order).data,
        })


class DesktopSyncMetricsView(APIView):
    """
    Reçoit les indicateurs de caisse et les données du magasin physique (LOGISZ Java Swing)
    pour consultation sécurisée en temps réel sur le smartphone du propriétaire.
    """
    permission_classes = [HasDesktopApiKey]

    @transaction.atomic
    def post(self, request):
        data = request.data or {}
        now = timezone.now()

        snapshot, _ = DesktopStoreSnapshot.objects.get_or_create(id=1)

        snapshot.today_date = data.get("today_date") or now.date()
        snapshot.chiffre_jour = to_dec(data.get("chiffre_jour"))
        snapshot.benefice_jour = to_dec(data.get("benefice_jour"))
        snapshot.chiffre_mois = to_dec(data.get("chiffre_mois"))
        snapshot.benefice_mois = to_dec(data.get("benefice_mois"))
        snapshot.chiffre_annee = to_dec(data.get("chiffre_annee"))
        snapshot.benefice_annee = to_dec(data.get("benefice_annee"))
        snapshot.caisse_espece = to_dec(data.get("caisse_espece"))
        snapshot.nbr_bons_jour = int(data.get("nbr_bons_jour") or 0)

        snapshot.total_creances_client = to_dec(data.get("total_creances_client"))
        snapshot.total_on_leur_doit = to_dec(data.get("total_on_leur_doit"))
        snapshot.total_dettes_fournisseur = to_dec(data.get("total_dettes_fournisseur"))
        snapshot.articles_en_alerte_count = int(data.get("articles_en_alerte_count") or 0)
        snapshot.articles_en_rupture_count = int(data.get("articles_en_rupture_count") or 0)

        # Synchronisation instantanée du snapshot clients (Stocké en JSON haute vitesse)
        clients_data = data.get("clients") or data.get("top_debtors") or []
        if clients_data:
            snapshot.top_debtors = clients_data

        if "history_7_days" in data:
            snapshot.history_7_days = data.get("history_7_days") or []
        if "top_debtors" in data:
            snapshot.top_debtors = data.get("top_debtors") or []
        if "recent_sales" in data:
            snapshot.recent_sales = data.get("recent_sales") or []
        if "recent_purchases" in data:
            snapshot.recent_purchases = data.get("recent_purchases") or []
        if "low_stock_items" in data:
            snapshot.low_stock_items = data.get("low_stock_items") or []

        snapshot.save()

        SyncLog.objects.create(
            direction="DESKTOP_TO_WEB",
            event_type="STORE_METRICS_SYNC",
            status="SUCCESS",
            summary=f"Métriques magasin reçues: CA jour={snapshot.chiffre_jour} DA, Caisse={snapshot.caisse_espece} DA, Créances={snapshot.total_creances_client} DA",
        )

        return Response({
            "status": "SUCCESS",
            "message": "Métriques magasin synchronisées avec succès.",
            "synced_at": snapshot.synced_at.isoformat(),
        })


# ============================================================================
# 6. WEBSITE ADMINISTRATION DASHBOARD ENDPOINTS
# ============================================================================

class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        recompute_reservations_and_conflicts()
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(physical_stock__lte=3).count()
        total_orders = OnlineOrder.objects.count()
        new_orders = OnlineOrder.objects.filter(status__in=["NEW", "PENDING"]).count()
        conflict_orders = OnlineOrder.objects.filter(has_stock_conflict=True, pos_converted=False).count()
        pos_converted_orders = OnlineOrder.objects.filter(pos_converted=True).count()

        revenue_agg = OnlineOrder.objects.exclude(status__in=["CANCELLED", "REJECTED"]).aggregate(
            total=Sum("total_amount")
        )
        total_online_revenue = float(revenue_agg["total"] or Decimal("0.00"))

        pending_installers = CustomerProfile.objects.filter(
            requested_type="INSTALLER", approval_status="PENDING"
        ).count()
        pending_resellers = CustomerProfile.objects.filter(
            requested_type="RESELLER", approval_status="PENDING"
        ).count()
        pending_reviews = Review.objects.filter(status="PENDING").count()

        recent_orders = OnlineOrder.objects.prefetch_related("items")[:10]
        recent_syncs = SyncLog.objects.all()[:15]

        return Response({
            "kpis": {
                "total_products": total_products,
                "low_stock_products": low_stock_products,
                "total_orders": total_orders,
                "new_orders": new_orders,
                "conflict_orders": conflict_orders,
                "pos_converted_orders": pos_converted_orders,
                "total_online_revenue": total_online_revenue,
                "pending_installers": pending_installers,
                "pending_resellers": pending_resellers,
                "pending_reviews": pending_reviews,
            },
            "recent_orders": OnlineOrderSerializer(recent_orders, many=True).data,
            "recent_sync_logs": SyncLogSerializer(recent_syncs, many=True).data,
        })


class AdminStoreMetricsView(APIView):
    """
    Renvoie les indicateurs et soldes du magasin physique au smartphone du propriétaire
    (authentifié par son code secret / JWT admin).
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        snapshot = DesktopStoreSnapshot.objects.first()
        if not snapshot:
            return Response({
                "has_data": False,
                "message": "Aucune synchronisation magasin reçue pour le moment."
            })
        data = DesktopStoreSnapshotSerializer(snapshot).data
        data["has_data"] = True
        return Response(data)


class AdminProductManageView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        qs = Product.objects.select_related("category", "brand").prefetch_related("images", "reviews").all()
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(reference__icontains=q) | Q(brand_raw__icontains=q))
        vis = request.query_params.get("visibility", "").strip().lower()
        if vis == "active":
            qs = qs.filter(is_active=True)
        elif vis == "hidden":
            qs = qs.filter(is_active=False)
        limit = int(request.query_params.get("limit", "600"))
        return Response(ProductSerializer(qs[:limit], many=True, context={"request": request}).data)

    def post(self, request):
        ser = AdminProductWriteSerializer(data=request.data)
        if ser.is_valid():
            prod = ser.save()
            return Response(ProductSerializer(prod, context={"request": request}).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        prod = Product.objects.filter(pk=pk).first()
        if not prod:
            return Response({"error": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)
        ser = AdminProductWriteSerializer(prod, data=request.data, partial=True)
        if ser.is_valid():
            prod = ser.save()
            return Response(ProductSerializer(prod, context={"request": request}).data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminProductImageManageView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, product_id):
        prod = Product.objects.filter(pk=product_id).first()
        if not prod:
            return Response({"error": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)

        image_url = ""
        # 1. Direct file upload
        if "image" in request.FILES:
            uploaded = request.FILES["image"]
            ext = os.path.splitext(uploaded.name)[1].lower() or ".jpg"
            filename = f"products/{prod.id}_{uuid.uuid4().hex[:8]}{ext}"
            saved = default_storage.save(filename, uploaded)
            image_url = f"{settings.MEDIA_URL}{saved}"
        # 2. Base64 file upload from client-side FileReader
        elif request.data.get("image_base64"):
            b64_str = str(request.data.get("image_base64", ""))
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            try:
                raw_bytes = base64.b64decode(b64_str)
                filename = f"products/{prod.id}_{uuid.uuid4().hex[:8]}.jpg"
                saved = default_storage.save(filename, ContentFile(raw_bytes))
                image_url = f"{settings.MEDIA_URL}{saved}"
            except Exception as e:
                return Response({"error": f"Image base64 invalide: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        # 3. External Image URL
        elif request.data.get("image_url"):
            image_url = str(request.data.get("image_url", "")).strip()

        if not image_url:
            return Response({"error": "Veuillez fournir une URL d'image ou sélectionner un fichier image."}, status=status.HTTP_400_BAD_REQUEST)

        is_main = bool(request.data.get("is_main", True))
        replace_all = bool(request.data.get("replace_all", False))

        if replace_all:
            prod.images.all().delete()
            is_main = True
        elif is_main or not prod.images.exists():
            prod.images.update(is_main=False)
            is_main = True

        img = ProductImage.objects.create(
            product=prod,
            image_url=image_url,
            alt_text=str(request.data.get("alt_text", prod.name)).strip(),
            is_main=is_main,
            sort_order=int(request.data.get("sort_order", 0)),
        )
        return Response({
            "message": "Photo mise à jour avec succès !",
            "image": ProductImageSerializer(img).data,
            "product": ProductSerializer(prod, context={"request": request}).data,
        }, status=status.HTTP_201_CREATED)

    def patch(self, request, product_id, image_id):
        img = ProductImage.objects.filter(pk=image_id, product_id=product_id).first()
        if not img:
            return Response({"error": "Image introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if request.data.get("is_main"):
            ProductImage.objects.filter(product_id=product_id).update(is_main=False)
            img.is_main = True
        if "sort_order" in request.data:
            img.sort_order = int(request.data["sort_order"])
        img.save()
        return Response(ProductImageSerializer(img).data)

    def delete(self, request, product_id, image_id):
        img = ProductImage.objects.filter(pk=image_id, product_id=product_id).first()
        if not img:
            return Response({"error": "Image introuvable."}, status=status.HTTP_404_NOT_FOUND)
        was_main = img.is_main
        img.delete()
        if was_main:
            first_rem = ProductImage.objects.filter(product_id=product_id).first()
            if first_rem:
                first_rem.is_main = True
                first_rem.save()
        return Response({"deleted": True})


class AdminAccountModerationView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        qs = CustomerProfile.objects.select_related("user").all().order_by("-created_at")
        status_filter = request.query_params.get("approval_status", "").strip().upper()
        if status_filter:
            qs = qs.filter(approval_status=status_filter)
        return Response(CustomerProfileSerializer(qs, many=True).data)

    def post(self, request, profile_id):
        profile = CustomerProfile.objects.select_related("user").filter(pk=profile_id).first()
        if not profile:
            return Response({"error": "Profil client introuvable."}, status=status.HTTP_404_NOT_FOUND)

        action = str(request.data.get("action", "")).strip().upper()
        new_type = str(request.data.get("account_type", "")).strip().upper()
        admin_notes = request.data.get("admin_notes")

        if new_type in ("PUBLIC", "INSTALLER", "RESELLER", "ADMIN"):
            profile.account_type = new_type
            profile.requested_type = new_type

        if action == "APPROVE":
            profile.approval_status = "APPROVED"
            if profile.requested_type in ("INSTALLER", "RESELLER"):
                profile.account_type = profile.requested_type
        elif action == "REJECT":
            profile.approval_status = "REJECTED"
            profile.account_type = "PUBLIC"
        elif action == "SUSPEND":
            profile.approval_status = "SUSPENDED"
        elif action == "SET_PUBLIC":
            profile.account_type = "PUBLIC"
            profile.approval_status = "NONE"

        if admin_notes is not None:
            profile.admin_notes = str(admin_notes)
        profile.save()
        return Response({
            "message": f"Compte {profile.user.username} mis à jour ({profile.effective_tier()} - {profile.approval_status}).",
            "profile": CustomerProfileSerializer(profile).data,
        })


class AdminReviewModerationView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        qs = Review.objects.select_related("product").all()
        st = request.query_params.get("status", "").strip().upper()
        if st:
            qs = qs.filter(status=st)
        return Response(ReviewSerializer(qs[:100], many=True).data)

    def post(self, request, review_id):
        rev = Review.objects.filter(pk=review_id).first()
        if not rev:
            return Response({"error": "Avis introuvable."}, status=status.HTTP_404_NOT_FOUND)
        action = str(request.data.get("action", "")).strip().upper()
        if action == "DELETE":
            rev.delete()
            return Response({"deleted": True})
        if action in ("APPROVED", "HIDDEN", "PENDING"):
            rev.status = action
        if "admin_reply" in request.data:
            rev.admin_reply = str(request.data["admin_reply"]).strip()
        rev.save()
        return Response(ReviewSerializer(rev).data)


class AdminCategoryBannerManageView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, resource_type):
        if resource_type == "categories":
            ser = CategorySerializer(data=request.data)
        elif resource_type == "brands":
            ser = BrandSerializer(data=request.data)
        elif resource_type == "banners":
            ser = BannerSerializer(data=request.data)
        else:
            return Response({"error": "Type invalide."}, status=status.HTTP_400_BAD_REQUEST)

        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)



# ============================================================================
# PHOTOS DU MAGASIN (galerie "Notre magasin" sur la page d'accueil)
# Fichiers stockes dans MEDIA_ROOT/store/ ; liste publique, ajout/suppression admin.
# ============================================================================
STORE_IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


class StorePhotosView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminOrStaff()]

    def _dir(self):
        d = os.path.join(settings.MEDIA_ROOT, "store")
        os.makedirs(d, exist_ok=True)
        return d

    def get(self, request):
        files = sorted(f for f in os.listdir(self._dir()) if f.lower().endswith(STORE_IMG_EXT))
        return Response({
            "photos": [f"{settings.MEDIA_URL}store/{f}" for f in files],
            "store": {
                "name": os.getenv("STORE_NAME", "INFOTECH ZEMRI"),
                "maps_url": os.getenv("STORE_MAPS_URL", "https://share.google/RJzeDOo33739eINyd"),
                "maps_query": os.getenv("STORE_MAPS_QUERY", "INFOTECH ZEMRI"),
                "address": os.getenv("STORE_ADDRESS", "4 Boulevard Didouche Mourad, Oran, Algérie"),
                "phone": "0557 88 27 19 / 0791 47 63 04",
                "phone_primary": "0557 88 27 19",
                "phone_secondary": "0791 47 63 04",
                "hours": os.getenv("STORE_HOURS", ""),
                "whatsapp": "+213557882719",
                "tiktok_url": os.getenv("STORE_TIKTOK_URL", "https://www.tiktok.com/@infotech.sz?is_from_webapp=1&sender_device=pc"),
            },
        })

    def post(self, request):
        up = request.FILES.get("image")
        raw = None
        ext = ".jpg"
        if up:
            ext = os.path.splitext(up.name)[1].lower() or ".jpg"
            raw = up.read()
        elif request.data.get("image_base64"):
            b64 = str(request.data["image_base64"])
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            raw = base64.b64decode(b64)
        if not raw or ext not in STORE_IMG_EXT:
            return Response({"error": "Image invalide."}, status=status.HTTP_400_BAD_REQUEST)
        name = f"magasin_{timezone.now():%Y%m%d%H%M%S}_{uuid.uuid4().hex[:6]}{ext}"
        with open(os.path.join(self._dir(), name), "wb") as fh:
            fh.write(raw)
        return Response({"url": f"{settings.MEDIA_URL}store/{name}"}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        name = os.path.basename(str(request.data.get("url", "") or request.query_params.get("url", "")))
        path = os.path.join(self._dir(), name)
        if name and os.path.isfile(path):
            os.remove(path)
            return Response({"deleted": name})
        return Response({"error": "Introuvable."}, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# NOEST DELIVERY PARTNER INTEGRATION VIEWS
# ============================================================================

class DeliveryWilayasView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            wilayas = noest_client.get_wilayas()
            fees = noest_client.get_fees()
            delivery_fees = fees.get("tarifs", {}).get("delivery", {})

            results = []
            for w in wilayas:
                w_code = str(w.get("code"))
                fee_info = delivery_fees.get(w_code, {})
                home_price = float(fee_info.get("tarif", 600))
                desk_price = float(fee_info.get("tarif_stopdesk", 300))
                results.append({
                    "id": int(w.get("code")),
                    "code": w.get("code"),
                    "name": w.get("nom"),
                    "home_fee": home_price,
                    "desk_fee": desk_price,
                    "is_active": w.get("is_active", 1) == 1
                })
            results.sort(key=lambda x: x["id"])
            return Response({"wilayas": results})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryCommunesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, wilaya_id):
        try:
            communes = noest_client.get_communes(wilaya_id)
            results = []
            for c in communes:
                results.append({
                    "id": c.get("id"),
                    "name": c.get("nom"),
                    "code_postal": c.get("code_postal"),
                    "is_active": c.get("is_active", 1) == 1
                })
            results.sort(key=lambda x: x["name"])
            return Response({"communes": results})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryDesksView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, wilaya_id):
        try:
            desks = noest_client.get_desks()
            w_str = f"{wilaya_id:02d}"
            matched = []
            for k, d in desks.items():
                if k.startswith(w_str):
                    matched.append({
                        "code": d.get("code"),
                        "name": d.get("name"),
                        "address": d.get("address"),
                        "commune": d.get("commune"),
                        "horaires": d.get("horaires"),
                        "map": d.get("map")
                    })
            return Response({"desks": matched})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryTrackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tracking_code):
        try:
            res = noest_client.track_noest_order(tracking_code.strip())
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminOrderSendNoestView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, order_uid):
        order = get_object_or_404(OnlineOrder, order_uid__iexact=order_uid.strip())
        wilaya_id = request.data.get("wilaya_id")
        commune = request.data.get("commune", "")
        stop_desk = request.data.get("stop_desk", 0)
        station_code = request.data.get("station_code", "")

        res = noest_client.create_noest_order(
            order=order,
            wilaya_id=wilaya_id,
            commune_name=commune,
            stop_desk=stop_desk,
            station_code=station_code
        )
        if res.get("success"):
            tracking = res.get("tracking", "")
            order.delivery_tracking = tracking
            order.delivery_status = "SENT_TO_NOEST"
            order.delivery_label_url = f"https://app.noest-dz.com/api/public/get/order/label?tracking={tracking}"
            order.delivery_error = ""
            order.save()
            return Response({"message": f"Colis créé chez NOEST avec succès ! N° {tracking}", "tracking": tracking})
        else:
            err = str(res.get("error", "Erreur lors de la création NOEST"))
            order.delivery_error = err
            order.save()
            return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)


class AdminOrderValidateNoestView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, order_uid):
        order = get_object_or_404(OnlineOrder, order_uid__iexact=order_uid.strip())
        if not order.delivery_tracking:
            return Response({"error": "Cette commande n'a pas encore de numéro de suivi NOEST."}, status=status.HTTP_400_BAD_REQUEST)

        res = noest_client.validate_noest_order(order.delivery_tracking)
        if res.get("success"):
            order.delivery_status = "VALIDATED_ON_NOEST"
            order.save()
            return Response({"message": "Commande validée pour la collecte logistique NOEST !"})
        else:
            return Response({"error": str(res.get("error", "Erreur validation"))}, status=status.HTTP_400_BAD_REQUEST)
