"""Miscellaneous utility helpers shared across the banking portal."""

import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from django.http import HttpRequest


def generate_uuid() -> str:
    """Return a new UUID4 as a canonical lowercase string."""
    return str(uuid.uuid4())


def to_decimal(value: Any) -> Decimal:
    """
    Safely convert *value* to :class:`~decimal.Decimal`.

    Always routes through ``str`` first to prevent floating-point
    representation issues (e.g. ``Decimal(0.1)`` → ambiguous binary fraction).

    Raises:
        ValueError: If *value* cannot be interpreted as a decimal number.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(
            f"Cannot convert {value!r} to Decimal: {exc}"
        ) from exc


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract the real client IP address from an HTTP request.

    Respects the ``X-Forwarded-For`` header added by reverse proxies.
    """
    x_forwarded_for: str | None = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
