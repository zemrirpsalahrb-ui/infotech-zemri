from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="storefront.html"), name="storefront-home"),
    path("mon-dashboard/", TemplateView.as_view(template_name="owner_dashboard.html"), name="owner-dashboard"),
    path("django-admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Production (Render) : servir aussi les photos produits / magasin
    from django.urls import re_path
    from django.views.static import serve
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

