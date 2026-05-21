import time
import json
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('api_request_logger')

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Structured JSON logging for every API request.
    Tracks duration, status, and generates/attaches a Request ID.
    """
    def process_request(self, request):
        request.start_time = time.time()
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration_ms = (time.time() - request.start_time) * 1000
        else:
            duration_ms = 0

        user_id = getattr(request.user, 'id', None)
        
        log_data = {
            'request_id': getattr(request, 'request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration_ms, 2),
            'user_id': user_id,
            'ip': self.get_client_ip(request),
        }

        logger.info(json.dumps(log_data))
        
        response['X-Request-ID'] = getattr(request, 'request_id', 'unknown')
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
