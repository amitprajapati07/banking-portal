import json
import logging
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class IdempotencyService:
    """
    Centralized service for managing API request idempotency using Redis.
    Valid for 24 hours.
    """
    TIMEOUT = 86400  # 24 hours

    @classmethod
    def get_key(cls, user_id, idempotency_key):
        return f"idempotency:{user_id}:{idempotency_key}"

    @classmethod
    def get_cached_response(cls, user_id, idempotency_key):
        key = cls.get_key(user_id, idempotency_key)
        return cache.get(key)

    @classmethod
    def cache_response(cls, user_id, idempotency_key, data, status_code):
        key = cls.get_key(user_id, idempotency_key)
        cache_data = {
            'data': data,
            'status': status_code
        }
        cache.set(key, cache_data, cls.TIMEOUT)

def idempotency_required(view_func):
    """
    Decorator for POST views that require an Idempotency-Key header.
    Currently applies to transfer operations.
    """
    @wraps(view_func)
    def wrapped_view(view_instance, request, *args, **kwargs):
        if request.method != 'POST':
            return view_func(view_instance, request, *args, **kwargs)

        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return view_func(view_instance, request, *args, **kwargs)

        user_id = request.user.id
        cached = IdempotencyService.get_cached_response(user_id, idempotency_key)
        
        if cached:
            logger.info(f"Replaying cached response for idempotency key: {idempotency_key}", 
                        extra={'user_id': user_id})
            return Response(cached['data'], status=cached['status'])

        response = view_func(view_instance, request, *args, **kwargs)
        
        # Only cache successful or client-error responses, not server errors
        if response.status_code < 500:
            IdempotencyService.cache_response(user_id, idempotency_key, response.data, response.status_code)
        
        return response
    return wrapped_view
