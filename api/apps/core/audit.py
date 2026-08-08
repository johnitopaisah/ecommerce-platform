"""
Helper for writing to AdminActionLog from admin-only views.
"""

from .models import AdminActionLog


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_admin_action(
    request,
    action: str,
    target: str,
    detail: dict | None = None,
    outcome: str = AdminActionLog.Outcome.SUCCESS,
):
    AdminActionLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        target=target,
        outcome=outcome,
        detail=detail or {},
        ip_address=_client_ip(request),
    )
