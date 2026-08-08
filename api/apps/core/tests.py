"""
Audit log viewer — read-only, permission-gated, and confirms the RBAC
denial-logging hook (apps.rbac.permissions) actually produces entries this
endpoint can see.
"""

import pytest
from django.contrib.auth.models import Group, Permission

from apps.rbac.models import RoleGrant
from .models import AdminActionLog

AUDIT_LOG_URL = '/api/v1/admin/audit-log/'


@pytest.fixture
def auditor(make_user):
    user = make_user(email='auditor@example.com', is_staff=True)
    group = Group.objects.create(name='Audit Log Viewer Test')
    group.permissions.add(
        Permission.objects.get(codename='view_audit_log', content_type__app_label='core')
    )
    RoleGrant.objects.create(user=user, group=group, expires_at=None)
    return user


@pytest.mark.django_db
class TestAuditLogList:
    def test_requires_view_audit_log_permission(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        response = api_client.get(AUDIT_LOG_URL)
        assert response.status_code == 403

    def test_qualified_user_can_view(self, api_client, auditor):
        AdminActionLog.objects.create(actor=auditor, action='test_action', target='Something')
        api_client.force_authenticate(auditor)

        response = api_client.get(AUDIT_LOG_URL)

        assert response.status_code == 200
        assert any(e['action'] == 'test_action' for e in response.data)

    def test_filters_by_outcome(self, api_client, auditor):
        AdminActionLog.objects.create(
            actor=auditor, action='denied_action', target='X', outcome=AdminActionLog.Outcome.DENIED,
        )
        AdminActionLog.objects.create(
            actor=auditor, action='ok_action', target='Y', outcome=AdminActionLog.Outcome.SUCCESS,
        )
        api_client.force_authenticate(auditor)

        response = api_client.get(AUDIT_LOG_URL, {'outcome': 'denied'})

        actions = [e['action'] for e in response.data]
        assert 'denied_action' in actions
        assert 'ok_action' not in actions

    def test_denied_permission_check_is_itself_logged_and_visible(self, api_client, auditor, regular_user):
        # Trigger a real denial via the RBAC layer (regular_user has no
        # permissions at all), then confirm the auditor can see it.
        api_client.force_authenticate(regular_user)
        api_client.get('/api/v1/admin/team/')  # 403, auto-logged

        api_client.force_authenticate(auditor)
        response = api_client.get(AUDIT_LOG_URL, {'outcome': 'denied'})

        assert any(e['action'] == 'permission_denied' for e in response.data)
