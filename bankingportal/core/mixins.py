"""Reusable DRF view mixins for the banking portal."""

from rest_framework.response import Response
from rest_framework import status


class SerializerContextMixin:
    """Pass the current ``request`` into every serializer's context."""

    def get_serializer_context(self) -> dict:
        context: dict = super().get_serializer_context()  # type: ignore[misc]
        context["request"] = self.request  # type: ignore[attr-defined]
        return context
