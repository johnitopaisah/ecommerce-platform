"""
Throttled JWT auth views.

SimpleJWT's TokenObtainPairView ships with no rate limiting — subclassed
here purely to attach a scoped throttle, since credential-stuffing against
/token/ is the highest-value brute-force target in the API.
"""

from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.throttles import LoginRateThrottle


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]
