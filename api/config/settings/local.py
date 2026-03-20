"""
Local/Minikube settings — extends production but disables HTTPS enforcement.
Used when DJANGO_SETTINGS_MODULE=config.settings.local
"""

from .production import *  # noqa: F401, F403

# ── Disable HTTPS enforcement for local/minikube ──────────────────────────────
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_PROXY_SSL_HEADER = None

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
