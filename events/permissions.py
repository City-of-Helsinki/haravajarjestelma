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


class AllowStatePatchOnly(BasePermission):
    """
    Allows to patch state field only.
    """

    def has_permission(self, request, view):
        allowed_fields = ["state"]
        has_allowed_fields_only = all(field in allowed_fields for field in request.data)
        return request.method == "PATCH" and has_allowed_fields_only


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
