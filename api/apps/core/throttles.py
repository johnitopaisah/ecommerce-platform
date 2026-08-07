"""
Scoped rate throttles for brute-force/enumeration-sensitive auth endpoints.

Each subclasses AnonRateThrottle (keyed by IP) since login, registration,
and password reset all happen before a user has a JWT — UserRateThrottle
would key by user, which doesn't help against credential stuffing from a
single IP against many accounts. Rates live in DEFAULT_THROTTLE_RATES.
"""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = 'auth_login'


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'auth_register'


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = 'auth_password_reset'


class ResendActivationRateThrottle(AnonRateThrottle):
    scope = 'auth_resend_activation'
