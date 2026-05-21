import logging
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class ConcurrentUpdateError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Record was modified by another request. Please retry."
    default_code = "CONCURRENT_UPDATE"

class RateLimitExceededError(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Rate limit exceeded."
    default_code = "RATE_LIMIT_EXCEEDED"

class FraudDetectedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Transaction flagged by fraud detection system."
    default_code = "FRAUD_DETECTED"

class InsufficientFundsError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Insufficient funds."
    default_code = "INSUFFICIENT_FUNDS"

class AccountNotActiveError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Account is frozen or closed."
    default_code = "ACCOUNT_NOT_ACTIVE"

class AccountOwnershipError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not own this account."
    default_code = "ACCOUNT_OWNERSHIP_ERROR"

def custom_exception_handler(exc, context):
    """
    Unified enterprise error response format.
    Includes request_id for observability.
    """
    response = exception_handler(exc, context)
    request = context.get('request')
    request_id = getattr(request, 'request_id', None)

    if response is not None:
        custom_data = {
            'error': getattr(exc, 'default_code', 'INTERNAL_ERROR').upper(),
            'detail': response.data.get('detail', str(exc)),
            'request_id': request_id
        }
        response.data = custom_data
    else:
        # For unhandled exceptions, log the stack trace and return a clean 500
        logger.exception("Unhandled server error", extra={'request_id': request_id})
        return Response({
            'error': 'SERVER_ERROR',
            'detail': 'An unexpected error occurred.',
            'request_id': request_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
