from rest_framework.throttling import UserRateThrottle

class TransferRateThrottle(UserRateThrottle):
    scope = 'transfer'

class LoginRateThrottle(UserRateThrottle):
    scope = 'login'
