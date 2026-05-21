"""Custom DRF permissions for the user_profiles app."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsOwnerOfProfile(BasePermission):
    """
    Object-level permission that allows access only to the profile owner.

    Used on ``/api/v1/users/me/`` type views to prevent cross-user access.
    """

    message = "You do not have permission to access this profile."

    def has_object_permission(
        self, request: Request, view, obj: object
    ) -> bool:
        return getattr(obj, "user", None) == request.user
