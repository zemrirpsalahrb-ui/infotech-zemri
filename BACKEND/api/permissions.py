import hmac
from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication


class SafeJWTAuthentication(JWTAuthentication):
    """
    Forgiving JWT authentication that returns None (anonymous user) instead of
    raising 401 AuthenticationFailed when an expired or malformed Bearer token
    is present in the browser's localStorage. Views that require authentication
    still enforce IsAuthenticated / IsAdminOrStaff via permission_classes.
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except Exception:
            return None



class IsAdminOrStaff(BasePermission):
    """Allows access only to staff/superuser or CustomerProfile with account_type='ADMIN'."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        profile = getattr(user, "profile", None)
        return bool(profile and profile.account_type == "ADMIN")


class HasDesktopApiKey(BasePermission):
    """
    Validates outbound requests initiated by the local Java Swing Desktop application
    using constant-time comparison on X-Desktop-API-Key header (or Admin JWT).
    """

    def has_permission(self, request, view):
        provided_key = request.headers.get("X-Desktop-API-Key", "").strip()
        expected_key = getattr(settings, "DESKTOP_SYNC_API_KEY", "").strip()
        if provided_key and expected_key and hmac.compare_digest(provided_key, expected_key):
            return True
        user = request.user
        if user and user.is_authenticated and (user.is_staff or user.is_superuser):
            return True
        return False

