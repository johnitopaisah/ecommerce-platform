"""
Production settings — extends base.
Used when DJANGO_SETTINGS_MODULE=config.settings.production
"""

import os

from .base import *  # noqa: F401, F403

DEBUG = False

# ── Security ──────────────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# CSRF_TRUSTED_ORIGINS must include the scheme — without it, Django rejects
# same-origin POSTs (e.g. the Django admin login form) whenever the request
# reaches the app over a different hop than the browser's (Cloudflare/Traefik
# terminate TLS in front of this pod, so Django sees the proxied request).
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'https://shopnow.johnisah.com').split(',')
    if origin.strip()
]

# ── GCS Media & Static ────────────────────────────────────────────────────────
# No service-account key required — this project's org policy blocks SA key
# creation, and the pod runs on a GCE VM whose attached service account
# (vm_sa, see terraform/modules/gcp_infra/main.tf) is picked up automatically
# via Application Default Credentials through the metadata server. Same
# ambient-auth pattern already used by the backup CronJobs.
USE_GCS = os.getenv('USE_GCS', 'False') == 'True'

if USE_GCS:
    GS_BUCKET_NAME = os.environ['GS_BUCKET_NAME']

    # STORAGES (Django 4.2+) rather than the legacy global GS_* settings —
    # 'default' (media) and 'staticfiles' need separate `location` prefixes
    # on the *same* bucket, which only per-backend OPTIONS can express;
    # global GS_LOCATION would apply to both and collide.
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
            'OPTIONS': {
                'bucket_name': GS_BUCKET_NAME,
                'location': 'media',
                'default_acl': None,       # uniform_bucket_level_access — no per-object ACLs
                'querystring_auth': False,  # public bucket — plain URLs, no signed params
                'file_overwrite': False,
            },
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
            'OPTIONS': {
                'bucket_name': GS_BUCKET_NAME,
                'location': 'static',
                'default_acl': None,
                'querystring_auth': False,
            },
        },
    }

    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

# ── Error tracking ────────────────────────────────────────────────────────────
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
        environment=os.getenv('ENVIRONMENT', 'production'),
    )

# ── Logging (JSON to stdout — picked up by k8s) ───────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
