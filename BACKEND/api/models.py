import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class CustomerProfile(models.Model):
    TYPE_CHOICES = [
        ("PUBLIC", "Client Public / Visiteur"),
        ("INSTALLER", "Installateur Professionnel"),
        ("RESELLER", "Revendeur / Grossiste"),
        ("ADMIN", "Administrateur"),
    ]
    STATUS_CHOICES = [
        ("NONE", "Aucune demande"),
        ("PENDING", "En attente d'approbation"),
        ("APPROVED", "Approuvé"),
        ("REJECTED", "Rejeté"),
        ("SUSPENDED", "Suspendu"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    account_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="PUBLIC")
    requested_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="PUBLIC")
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NONE")
    phone = models.CharField(max_length=30, blank=True, default="")
    company_name = models.CharField(max_length=150, blank=True, default="")
    wilaya = models.CharField(max_length=80, blank=True, default="")
    address = models.TextField(blank=True, default="")
    rc_number = models.CharField(max_length=80, blank=True, default="", help_text="Registre de Commerce")
    nif_number = models.CharField(max_length=80, blank=True, default="", help_text="Numéro d'Identification Fiscale")
    professional_justification = models.TextField(blank=True, default="", db_column="prof_justification")
    admin_notes = models.TextField(blank=True, default="")
    desktop_client_name = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def effective_tier(self) -> str:
        """
        Pending, rejected, or suspended accounts MUST continue seeing public prices.
        Only approved Installers / Resellers receive their tier pricing.
        """
        if self.user.is_staff or self.user.is_superuser or self.account_type == "ADMIN":
            return "RESELLER"
        if self.approval_status == "APPROVED" and self.account_type in ("INSTALLER", "RESELLER"):
            return self.account_type
        return "PUBLIC"

    def __str__(self):
        return f"{self.user.username} ({self.effective_tier()} - {self.approval_status})"


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    icon_name = models.CharField(max_length=60, blank=True, default="Camera")
    image_url = models.URLField(max_length=500, blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or f"cat-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo_url = models.URLField(max_length=500, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_featured = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or f"brand-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    KIT_COMPONENT_CHOICES = [
        ("NONE", "Standard"),
        ("CAMERA", "Caméra de surveillance"),
        ("RECORDER", "Enregistreur DVR / XVR / NVR"),
        ("HDD", "Disque Dur Surveillance"),
        ("PSU", "Alimentation électrique"),
        ("CABLE", "Câble Coaxial / Réseau"),
        ("CONNECTOR", "Connecteur BNC / RJ45 / Balun"),
        ("ACCESSORY", "Boîte de jonction / Accessoire"),
        ("COMPLETE_KIT", "Kit Complet CCTV"),
    ]
    KIT_TECH_CHOICES = [
        ("ALL", "Universel (IP & Analogique HD)"),
        ("ANALOG_HD", "Analogique HD / HDCVI / HDTVI / AHD"),
        ("IP", "IP Réseau PoE"),
        ("WIFI", "Sans-fil Wi-Fi"),
    ]

    # Primary Desktop Link (Source of truth: MariaDB inventair)
    desktop_ide = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    reference = models.CharField(max_length=60, unique=True, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=230, unique=True, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    brand_raw = models.CharField(max_length=80, blank=True, default="")

    # Multi-tier Pricing (DA)
    public_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    installer_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    reseller_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    promo_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    special_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    tva_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("19.00"))

    # Stock & Reservation (Desktop is primary source of truth for physical_stock)
    physical_stock = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    reserved_stock = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("3.00"))

    # Website-enriched content (Owned by Website Admin / Neon)
    short_description = models.CharField(max_length=400, blank=True, default="")
    description = models.TextField(blank=True, default="")
    technical_specs = models.JSONField(default=dict, blank=True)
    warranty_months = models.IntegerField(default=12)

    # CCTV Kit Builder & Compatibility metadata
    kit_component_type = models.CharField(max_length=30, choices=KIT_COMPONENT_CHOICES, default="NONE")
    kit_technology = models.CharField(max_length=20, choices=KIT_TECH_CHOICES, default="ALL")
    kit_channels = models.IntegerField(default=0, help_text="4, 8, 16, 32 channels for DVR/NVR")
    compatibility_notes = models.CharField(max_length=300, blank=True, default="")

    # Merchandising flags
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_special_offer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    last_desktop_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-is_bestseller", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.name}-{self.reference}") or f"prod-{uuid.uuid4().hex[:8]}"
            self.slug = base[:220]
        if self.installer_price <= 0 and self.public_price > 0:
            if self.reseller_price > 0 and self.reseller_price < self.public_price:
                # Default installer price halfway between public and reseller or equal to reseller
                self.installer_price = self.reseller_price
            else:
                self.installer_price = (self.public_price * Decimal("0.92")).quantize(Decimal("0.01"))
        if self.reseller_price <= 0 and self.public_price > 0:
            self.reseller_price = (self.public_price * Decimal("0.88")).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    @property
    def available_stock(self) -> Decimal:
        avail = self.physical_stock - self.reserved_stock
        return avail if avail > Decimal("0.00") else Decimal("0.00")

    def get_unit_price_for_tier(self, tier: str) -> Decimal:
        """
        Server-side authoritative price calculation.
        Never trust a price submitted by the frontend.
        """
        candidates = [self.public_price]
        if self.promo_price and self.promo_price > Decimal("0.00"):
            candidates.append(self.promo_price)
        if tier in ("INSTALLER", "RESELLER") and self.installer_price > Decimal("0.00"):
            candidates.append(self.installer_price)
        if tier == "RESELLER" and self.reseller_price > Decimal("0.00"):
            candidates.append(self.reseller_price)
        if tier in ("INSTALLER", "RESELLER") and self.special_price and self.special_price > Decimal("0.00"):
            candidates.append(self.special_price)
        valid = [c for c in candidates if c > Decimal("0.00")]
        return min(valid) if valid else self.public_price

    def __str__(self):
        return f"[{self.reference}] {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=600)
    cloudinary_public_id = models.CharField(max_length=200, blank=True, default="")
    alt_text = models.CharField(max_length=200, blank=True, default="")
    is_main = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_main", "sort_order", "id"]

    def __str__(self):
        return f"Image for {self.product.reference} (main={self.is_main})"


class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=350, blank=True, default="")
    badge_text = models.CharField(max_length=80, blank=True, default="OFFRE PRO CCTV")
    cta_text = models.CharField(max_length=80, blank=True, default="Explorer le catalogue")
    cta_link = models.CharField(max_length=250, blank=True, default="/catalog")
    image_url = models.URLField(max_length=600, blank=True, default="")
    accent_color = models.CharField(max_length=30, blank=True, default="#3B82F6")
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-id"]

    def __str__(self):
        return self.title


class Review(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "En attente de modération"),
        ("APPROVED", "Approuvé"),
        ("HIDDEN", "Masqué"),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews")
    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=180, blank=True, default="")
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    admin_reply = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.reference} - {self.rating}/5 by {self.author_name}"


class OnlineOrder(models.Model):
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("PREPARING", "Preparing"),
        ("READY_FOR_PICKUP", "Ready for Pickup"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
        ("REJECTED", "Rejected"),
    ]
    DELIVERY_CHOICES = [
        ("DELIVERY", "Livraison à domicile / entreprise"),
        ("PICKUP", "Retrait au magasin (Store Pickup)"),
    ]
    PAYMENT_CHOICES = [
        ("CASH_ON_DELIVERY", "Paiement à la livraison (Espèces)"),
        ("PAY_AT_STORE", "Paiement au comptoir du magasin"),
        ("BANK_TRANSFER", "Virement bancaire / CCP"),
        ("CIB_EDAHABIA", "Carte CIB / Edahabia"),
    ]

    order_uid = models.CharField(max_length=40, unique=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    # Customer Information Snapshot
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=40)
    customer_email = models.EmailField(blank=True, default="")
    company_name = models.CharField(max_length=150, blank=True, default="")
    wilaya = models.CharField(max_length=80, blank=True, default="Alger")
    delivery_address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    applied_tier = models.CharField(max_length=20, default="PUBLIC")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default="DELIVERY")
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default="CASH_ON_DELIVERY")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="NEW", db_index=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    shipping_fee = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    # Stock Reservation & Conflict Prevention
    reservation_active = models.BooleanField(default=False)
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    has_stock_conflict = models.BooleanField(default=False)
    conflict_details = models.TextField(blank=True, default="")

    # Desktop POS Conversion Tracking (Prevents double stock deduction!)
    pos_converted = models.BooleanField(default=False, db_index=True)
    pos_bon_number = models.CharField(max_length=40, blank=True, default="")
    pos_converted_at = models.DateTimeField(null=True, blank=True)
    pos_converted_by = models.CharField(max_length=80, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_uid} - {self.customer_name} ({self.status})"


class OnlineOrderItem(models.Model):
    order = models.ForeignKey(OnlineOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    desktop_ide = models.IntegerField(null=True, blank=True)
    product_reference = models.CharField(max_length=60)
    product_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("1.00"))
    applied_unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    public_unit_price_snapshot = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = (self.quantity * self.applied_unit_price).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_uid}: {self.quantity}x {self.product_reference} @ {self.applied_unit_price}"


class SyncLog(models.Model):
    sync_uid = models.CharField(max_length=64, default=uuid.uuid4, unique=True)
    idempotency_key = models.CharField(max_length=120, unique=True, null=True, blank=True)
    direction = models.CharField(max_length=30, default="DESKTOP_TO_WEB")
    event_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="SUCCESS")
    summary = models.CharField(max_length=300)
    details = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.created_at}] {self.direction} {self.event_type}: {self.status}"
