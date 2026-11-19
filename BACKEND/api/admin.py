from django.contrib import admin
from django.utils.html import format_html
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
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image_url", "is_main", "sort_order", "image_preview"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 4px;" />', obj.image_url)
        return "—"
    image_preview.short_description = "Aperçu"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["reference", "name", "category", "public_price", "reseller_price", "physical_stock", "image_thumbnail"]
    search_fields = ["reference", "name", "brand_raw"]
    list_filter = ["category", "brand", "is_active"]
    inlines = [ProductImageInline]

    def image_thumbnail(self, obj):
        img = obj.images.filter(is_main=True).first() or obj.images.first()
        if img and img.image_url:
            return format_html('<img src="{}" style="max-height: 40px; border-radius: 4px;" />', img.image_url)
        return "—"
    image_thumbnail.short_description = "Photo"


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "account_type", "requested_type", "approval_status", "phone", "company_name"]
    list_filter = ["account_type", "approval_status"]
    search_fields = ["user__username", "company_name", "phone"]


@admin.register(OnlineOrder)
class OnlineOrderAdmin(admin.ModelAdmin):
    list_display = ["order_uid", "customer_name", "customer_phone", "applied_tier", "total_amount", "status", "pos_converted", "pos_bon_number"]
    list_filter = ["status", "pos_converted", "applied_tier"]
    search_fields = ["order_uid", "customer_name", "customer_phone", "pos_bon_number"]


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(ProductImage)
admin.site.register(Banner)
admin.site.register(Review)
admin.site.register(OnlineOrderItem)
admin.site.register(SyncLog)
