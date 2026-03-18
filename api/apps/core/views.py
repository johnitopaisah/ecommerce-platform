"""
Health and readiness check views.

GET /api/v1/health/   — liveness probe  (is the process up?)
GET /api/v1/ready/    — readiness probe (are DB + cache reachable?)
"""

from django.db import connection, OperationalError as DbError
from django_redis import get_redis_connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema


@extend_schema(tags=['health'])
@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """Liveness probe — always returns 200 if the process is running."""
    return Response({'status': 'ok'})


@extend_schema(tags=['health'])
@api_view(['GET'])
@permission_classes([AllowAny])
def ready(request):
    """
    Readiness probe — checks DB and Redis connectivity.
    Returns 200 when both are reachable, 503 otherwise.
    """
    checks = {}

    # Database check
    try:
        connection.ensure_connection()
        checks['db'] = 'ok'
    except DbError as exc:
        checks['db'] = f'error: {exc}'

    # Redis / cache check
    try:
        redis_conn = get_redis_connection('default')
        redis_conn.ping()
        checks['cache'] = 'ok'
    except Exception as exc:
        checks['cache'] = f'error: {exc}'

    all_ok = all(v == 'ok' for v in checks.values())
    http_status = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return Response({'status': 'ok' if all_ok else 'degraded', **checks}, status=http_status)
