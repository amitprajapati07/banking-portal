"""Object-level permissions for the accounts app."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.accounts.models import Account


class IsAccountOwner(BasePermission):
    """
    Object-level permission that restricts access to the account owner.

    Applied to:
      - Retrieve account detail (GET /accounts/{id}/)
      - Change account status (PATCH /accounts/{id}/status/)
    """

    message = "You do not own this account."

    def has_object_permission(
        self, request: Request, view, obj: Account
    ) -> bool:
        return obj.owner == request.user
