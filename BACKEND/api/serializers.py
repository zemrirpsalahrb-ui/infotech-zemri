from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework import serializers
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


def get_request_tier(request) -> str:
    if not request or not hasattr(request, "user") or not request.user.is_authenticated:
        return "PUBLIC"
    user = request.user
    if user.is_staff or user.is_superuser:
        return "RESELLER"
    profile = getattr(user, "profile", None)
    return profile.effective_tier() if profile else "PUBLIC"


class CustomerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    effective_tier = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "account_type",
            "requested_type",
            "approval_status",
            "effective_tier",
            "is_admin",
            "phone",
            "company_name",
            "wilaya",
            "address",
            "rc_number",
            "nif_number",
            "professional_justification",
            "admin_notes",
            "desktop_client_name",
            "desktop_client_id",
            "desktop_balance",
            "last_invoice",
            "created_at",
        ]

    def get_effective_tier(self, obj):
        return obj.effective_tier()

    def get_is_admin(self, obj):
        return bool(obj.user.is_staff or obj.user.is_superuser or obj.account_type == "ADMIN")


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon_name",
            "image_url",
            "sort_order",
            "is_active",
            "product_count",
        ]


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "slug",
            "logo_url",
            "description",
            "is_featured",
            "sort_order",
            "product_count",
        ]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            "id",
            "product",
            "image_url",
            "cloudinary_public_id",
            "alt_text",
            "is_main",
            "sort_order",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_reference = serializers.CharField(source="product.reference", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "product_name",
            "product_reference",
            "author_name",
            "rating",
            "title",
            "comment",
            "is_verified_purchase",
            "status",
            "admin_reply",
            "created_at",
        ]
        read_only_fields = ["is_verified_purchase", "status", "admin_reply", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default="Sécurité & CCTV")
    category_slug = serializers.CharField(source="category.slug", read_only=True, default="cctv")
    brand_name = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    main_image = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    effective_price = serializers.SerializerMethodField()
    applied_tier = serializers.SerializerMethodField()
    tier_prices = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    approved_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "desktop_ide",
            "reference",
            "name",
            "slug",
            "category",
            "category_name",
            "category_slug",
            "brand",
            "brand_name",
            "brand_raw",
            "public_price",
            "promo_price",
            "effective_price",
            "applied_tier",
            "tier_prices",
            "tva_rate",
            "physical_stock",
            "reserved_stock",
            "available_stock",
            "in_stock",
            "short_description",
            "description",
            "technical_specs",
            "warranty_months",
            "kit_component_type",
            "kit_technology",
            "kit_channels",
            "compatibility_notes",
            "is_featured",
            "is_bestseller",
            "is_new_arrival",
            "is_special_offer",
            "is_active",
            "main_image",
            "images",
            "avg_rating",
            "review_count",
            "approved_reviews",
            "last_desktop_sync",
        ]

    def get_brand_name(self, obj):
        if obj.brand:
            return obj.brand.name
        return obj.brand_raw if obj.brand_raw and obj.brand_raw.lower() != "b" else "LOGISZ PRO"

    def get_main_image(self, obj):
        imgs = list(obj.images.all())
        if imgs:
            main = next((i for i in imgs if i.is_main), imgs[0])
            return main.image_url
        return ""

    def get_available_stock(self, obj):
        return float(obj.available_stock)

    def get_in_stock(self, obj):
        return obj.available_stock > Decimal("0.00")

    def get_applied_tier(self, obj):
        request = self.context.get("request")
        return get_request_tier(request)

    def get_effective_price(self, obj):
        request = self.context.get("request")
        tier = get_request_tier(request)
        return float(obj.get_unit_price_for_tier(tier))

    def get_tier_prices(self, obj):
        """
        Only expose wholesale/installer/reseller prices to authorized tiers or admins.
        Pending or guest users only see public & promo prices.
        """
        request = self.context.get("request")
        tier = get_request_tier(request)
        user = getattr(request, "user", None)
        is_admin = bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
        data = {
            "public_price": float(obj.public_price),
            "promo_price": float(obj.promo_price) if obj.promo_price else None,
        }
        if tier in ("INSTALLER", "RESELLER") or is_admin:
            data["installer_price"] = float(obj.installer_price)
        if tier == "RESELLER" or is_admin:
            data["reseller_price"] = float(obj.reseller_price)
            data["special_price"] = float(obj.special_price) if obj.special_price else None
        return data

    def get_avg_rating(self, obj):
        approved = [r.rating for r in obj.reviews.all() if r.status == "APPROVED"]
        if not approved:
            return 4.9
        return round(sum(approved) / len(approved), 1)

    def get_review_count(self, obj):
        return sum(1 for r in obj.reviews.all() if r.status == "APPROVED")

    def get_approved_reviews(self, obj):
        if not self.context.get("include_reviews", False):
            return []
        approved = [r for r in obj.reviews.all() if r.status == "APPROVED"]
        return ReviewSerializer(approved, many=True).data


class AdminProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"


class OnlineOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineOrderItem
        fields = [
            "id",
            "product",
            "desktop_ide",
            "product_reference",
            "product_name",
            "quantity",
            "applied_unit_price",
            "public_unit_price_snapshot",
            "line_total",
        ]


class OnlineOrderSerializer(serializers.ModelSerializer):
    items = OnlineOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = OnlineOrder
        fields = [
            "id",
            "order_uid",
            "idempotency_key",
            "customer_name",
            "customer_phone",
            "customer_email",
            "company_name",
            "wilaya",
            "delivery_address",
            "delivery_commune",
            "delivery_stop_desk",
            "delivery_station_code",
            "delivery_tracking",
            "delivery_status",
            "delivery_label_url",
            "delivery_error",
            "notes",
            "applied_tier",
            "delivery_method",
            "payment_method",
            "status",
            "subtotal",
            "shipping_fee",
            "total_amount",
            "reservation_active",
            "reservation_expires_at",
            "has_stock_conflict",
            "conflict_details",
            "pos_converted",
            "pos_bon_number",
            "pos_converted_at",
            "pos_converted_by",
            "items",
            "created_at",
            "updated_at",
        ]


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = "__all__"


class DesktopStoreSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesktopStoreSnapshot
        fields = "__all__"

