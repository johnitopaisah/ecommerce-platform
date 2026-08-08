"""
Admin-only audit log viewer. Read-only, full stop — nothing here is ever
edited or deleted through the API, matching AdminActionLog's append-only
guarantee at the model layer.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.rbac.permissions import RequiresPermission
from .models import AdminActionLog
from .serializers import AdminActionLogSerializer


@extend_schema(tags=['admin'])
@api_view(['GET'])
@permission_classes([RequiresPermission('core.view_audit_log')])
def admin_audit_log_list(request):
    entries = AdminActionLog.objects.select_related('actor').order_by('-created')

    actor_id = request.query_params.get('actor')
    if actor_id:
        entries = entries.filter(actor_id=actor_id)

    action = request.query_params.get('action')
    if action:
        entries = entries.filter(action=action)

    outcome = request.query_params.get('outcome')
    if outcome:
        entries = entries.filter(outcome=outcome)

    search = request.query_params.get('search', '').strip()
    if search:
        entries = entries.filter(target__icontains=search)

    # Simple cap rather than full pagination — this is an operational/
    # security tool, not a paginated business list; most-recent-first with
    # a generous limit covers the real "what just happened" use case.
    return Response(AdminActionLogSerializer(entries[:500], many=True).data)
