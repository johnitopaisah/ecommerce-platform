"""
Development settings — extends base.
Used when DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# Allow browsable API in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

# In development, allow all origins so user-ui and admin-ui can talk to the API
# without needing to whitelist specific ports.
CORS_ALLOW_ALL_ORIGINS = True

# Use local filesystem for media (not S3)
USE_S3 = False

# ── Optional: SQL query logging ────────────────────────────────────────────────
# Uncomment to log all DB queries to the console during development.
# LOGGING = {
#     'version': 1,
#     'filters': {'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'}},
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#         }
#     },
# }
