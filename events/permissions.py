from rest_framework.permissions import BasePermission, SAFE_METHODS


class ReadOnly(BasePermission):
    """
    Allows read-only operations only.
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class AllowPost(BasePermission):
    """
    Allows post method only.
    """

    def has_permission(self, request, view):
        return request.method == "POST"


class IsOfficial(BasePermission):
    """
    Allows access only to officials.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and hasattr(request.user, "is_official")
            and request.user.is_official
        )


class IsSuperUser(BasePermission):
    """
    Allows access only to superusers.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
