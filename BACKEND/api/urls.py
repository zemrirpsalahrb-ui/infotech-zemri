from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    HomeCatalogView,
    ProductListView,
    ProductDetailView,
    ProductReviewCreateView,
    KitBuilderEvaluateView,
    RegisterView,
    LoginView,
    MeView,
    CheckoutOrderView,
    OrderTrackView,
    DesktopSyncProductsView,
    DesktopOrdersListView,
    DesktopOrderStatusUpdateView,
    DesktopOrderConvertPosView,
    AdminDashboardStatsView,
    AdminProductManageView,
    AdminProductImageManageView,
    AdminAccountModerationView,
    AdminReviewModerationView,
    AdminCategoryBannerManageView,
    StorePhotosView,
)

urlpatterns = [
    # Public & Catalog
    path("store/photos/", StorePhotosView.as_view(), name="store-photos"),
    path("catalog/home/", HomeCatalogView.as_view(), name="catalog-home"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:product_id>/reviews/", ProductReviewCreateView.as_view(), name="product-review-create"),
    path("products/<str:lookup>/", ProductDetailView.as_view(), name="product-detail"),

    # CCTV Kit Builder
    path("kit-builder/", KitBuilderEvaluateView.as_view(), name="kit-builder"),

    # Authentication & Customer Accounts
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),

    # Checkout & Orders
    path("orders/checkout/", CheckoutOrderView.as_view(), name="orders-checkout"),
    path("orders/track/<str:order_uid>/", OrderTrackView.as_view(), name="orders-track"),

    # Desktop Software Outbound Synchronization API (X-Desktop-API-Key)
    path("desktop/sync-products/", DesktopSyncProductsView.as_view(), name="desktop-sync-products"),
    path("desktop/orders/", DesktopOrdersListView.as_view(), name="desktop-orders-list"),
    path("desktop/orders/<str:order_uid>/status/", DesktopOrderStatusUpdateView.as_view(), name="desktop-order-status"),
    path("desktop/orders/<str:order_uid>/convert-pos/", DesktopOrderConvertPosView.as_view(), name="desktop-order-convert-pos"),

    # Website Administration Dashboard API
    path("admin/dashboard/", AdminDashboardStatsView.as_view(), name="admin-dashboard"),
    path("admin/products/", AdminProductManageView.as_view(), name="admin-products"),
    path("admin/products/<int:pk>/", AdminProductManageView.as_view(), name="admin-product-detail"),
    path("admin/products/<int:product_id>/images/", AdminProductImageManageView.as_view(), name="admin-product-images"),
    path("admin/products/<int:product_id>/images/<int:image_id>/", AdminProductImageManageView.as_view(), name="admin-product-image-detail"),
    path("admin/accounts/", AdminAccountModerationView.as_view(), name="admin-accounts"),
    path("admin/accounts/<int:profile_id>/moderate/", AdminAccountModerationView.as_view(), name="admin-account-moderate"),
    path("admin/reviews/", AdminReviewModerationView.as_view(), name="admin-reviews"),
    path("admin/reviews/<int:review_id>/moderate/", AdminReviewModerationView.as_view(), name="admin-review-moderate"),
    path("admin/resources/<str:resource_type>/", AdminCategoryBannerManageView.as_view(), name="admin-resources"),
]


