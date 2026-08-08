"""
Grant/approval workflow tests — services.py (the security rules) and the
API surface built on top of it. Split from tests.py (permission resolution)
since this is a distinct layer with its own fixtures.
"""

from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core.models import AdminActionLog
from . import services
from .models import RoleGrant, RoleGrantRequest

ROLES_URL = '/api/v1/rbac/roles/'
REQUESTS_URL = '/api/v1/rbac/requests/'
PENDING_URL = '/api/v1/rbac/requests/pending/'
MY_PERMISSIONS_URL = '/api/v1/rbac/me/permissions/'
GRANTS_URL = '/api/v1/rbac/grants/'


@pytest.fixture
def inventory_perm(db):
    return Permission.objects.get(codename='manage_inventory', content_type__app_label='store')


@pytest.fixture
def pricing_perm(db):
    return Permission.objects.get(codename='manage_pricing', content_type__app_label='store')


@pytest.fixture
def inventory_role(db, inventory_perm):
    group = Group.objects.create(name='Inventory Only')
    group.permissions.add(inventory_perm)
    return group


@pytest.fixture
def full_store_role(db, inventory_perm, pricing_perm):
    group = Group.objects.create(name='Full Store')
    group.permissions.add(inventory_perm, pricing_perm)
    return group


@pytest.fixture
def manager_with_full_store(make_user, full_store_role):
    """A user who already holds every permission Full Store grants —
    qualified under the subset rule to approve requests for it or for
    anything narrower, like Inventory Only. Deliberately NOT built on the
    shared `regular_user` fixture — tests need requester and approver to
    be distinct people, or self-approval rejection masks everything else."""
    manager = make_user(email='manager@example.com')
    RoleGrant.objects.create(user=manager, group=full_store_role, expires_at=None)
    return manager


@pytest.mark.django_db
class TestRequestRole:
    def test_creates_pending_request(self, regular_user, inventory_role):
        req = services.request_role(regular_user, inventory_role, duration_hours=4, justification='testing')
        assert req.status == RoleGrantRequest.Status.PENDING
        assert req.duration_hours == 4

    def test_blank_justification_rejected(self, regular_user, inventory_role):
        with pytest.raises(ValidationError):
            services.request_role(regular_user, inventory_role, duration_hours=None, justification='   ')


@pytest.mark.django_db
class TestApproveRequest:
    def test_qualified_approver_creates_a_time_bounded_grant(
        self, regular_user, make_user, inventory_role, manager_with_full_store,
    ):
        requester = make_user(email='requester@example.com')
        req = services.request_role(requester, inventory_role, duration_hours=4, justification='need it')

        grant = services.approve_request(req, manager_with_full_store)

        assert grant.user == requester
        assert grant.group == inventory_role
        assert grant.expires_at is not None
        assert grant.expires_at <= timezone.now() + timedelta(hours=4, minutes=1)
        req.refresh_from_db()
        assert req.status == RoleGrantRequest.Status.APPROVED
        assert req.resulting_grant == grant

    def test_permanent_request_creates_permanent_grant(self, make_user, inventory_role, manager_with_full_store):
        requester = make_user(email='requester2@example.com')
        req = services.request_role(requester, inventory_role, duration_hours=None, justification='permanent need')

        grant = services.approve_request(req, manager_with_full_store)

        assert grant.expires_at is None

    def test_cannot_approve_own_request(self, manager_with_full_store, inventory_role):
        req = services.request_role(manager_with_full_store, inventory_role, None, 'for myself')
        with pytest.raises(PermissionDenied):
            services.approve_request(req, manager_with_full_store)

    def test_approver_without_subset_permissions_is_rejected(self, regular_user, make_user, full_store_role):
        # regular_user holds nothing — cannot approve a request for a role
        # whose permissions they don't themselves have.
        requester = make_user(email='requester3@example.com')
        req = services.request_role(requester, full_store_role, None, 'need full access')

        with pytest.raises(PermissionDenied):
            services.approve_request(req, regular_user)

    def test_narrower_role_approvable_by_broader_holder(
        self, make_user, inventory_role, manager_with_full_store,
    ):
        # manager holds Full Store (inventory + pricing) — a subset of that
        # covers Inventory Only, so they should qualify.
        requester = make_user(email='requester4@example.com')
        req = services.request_role(requester, inventory_role, None, 'just inventory')

        grant = services.approve_request(req, manager_with_full_store)
        assert grant.group == inventory_role

    def test_already_decided_request_cannot_be_approved_again(
        self, make_user, inventory_role, manager_with_full_store,
    ):
        requester = make_user(email='requester5@example.com')
        req = services.request_role(requester, inventory_role, None, 'need it')
        services.approve_request(req, manager_with_full_store)

        with pytest.raises(ValidationError):
            services.approve_request(req, manager_with_full_store)

    def test_superuser_can_approve_anything(self, make_user, full_store_role):
        superuser = make_user(email='super@example.com', is_superuser=True, is_staff=True)
        requester = make_user(email='requester6@example.com')
        req = services.request_role(requester, full_store_role, None, 'need it')

        grant = services.approve_request(req, superuser)
        assert grant.group == full_store_role


@pytest.mark.django_db
class TestDenyAndCancel:
    def test_deny_marks_request_denied(self, make_user, inventory_role, manager_with_full_store):
        requester = make_user(email='requester7@example.com')
        req = services.request_role(requester, inventory_role, None, 'need it')

        services.deny_request(req, manager_with_full_store, decision_reason='not needed')

        req.refresh_from_db()
        assert req.status == RoleGrantRequest.Status.DENIED
        assert req.decision_reason == 'not needed'

    def test_cannot_deny_own_request(self, manager_with_full_store, inventory_role):
        req = services.request_role(manager_with_full_store, inventory_role, None, 'for myself')
        with pytest.raises(PermissionDenied):
            services.deny_request(req, manager_with_full_store)

    def test_requester_can_cancel_own_pending_request(self, regular_user, inventory_role):
        req = services.request_role(regular_user, inventory_role, None, 'changed my mind')
        services.cancel_request(req, regular_user)
        req.refresh_from_db()
        assert req.status == RoleGrantRequest.Status.CANCELLED

    def test_other_user_cannot_cancel_someone_elses_request(self, regular_user, make_user, inventory_role):
        other = make_user(email='other@example.com')
        req = services.request_role(regular_user, inventory_role, None, 'mine')
        with pytest.raises(PermissionDenied):
            services.cancel_request(req, other)


@pytest.mark.django_db
class TestRevokeGrant:
    def test_qualified_user_can_revoke(self, make_user, inventory_role, manager_with_full_store):
        holder = make_user(email='holder@example.com')
        grant = RoleGrant.objects.create(user=holder, group=inventory_role, expires_at=None)

        services.revoke_grant(grant, manager_with_full_store)

        grant.refresh_from_db()
        assert grant.status == RoleGrant.Status.REVOKED
        assert grant.is_currently_valid is False

    def test_unqualified_user_cannot_revoke(self, regular_user, make_user, inventory_role):
        holder = make_user(email='holder2@example.com')
        grant = RoleGrant.objects.create(user=holder, group=inventory_role, expires_at=None)
        with pytest.raises(PermissionDenied):
            services.revoke_grant(grant, regular_user)


@pytest.mark.django_db
class TestSetRolePermissions:
    def test_non_superuser_cannot_grant_beyond_own_permissions(self, regular_user, inventory_perm):
        group = Group.objects.create(name='Overreach Test')
        with pytest.raises(PermissionDenied):
            services.set_role_permissions(group, ['store.manage_inventory'], regular_user)

    def test_non_superuser_can_grant_within_own_permissions(self, manager_with_full_store):
        group = Group.objects.create(name='Subset Test')
        services.set_role_permissions(group, ['store.manage_inventory'], manager_with_full_store)
        assert group.permissions.filter(codename='manage_inventory').exists()

    def test_superuser_can_grant_anything(self, make_user):
        superuser = make_user(email='super3@example.com', is_superuser=True, is_staff=True)
        group = Group.objects.create(name='Superuser Test')
        services.set_role_permissions(group, ['store.manage_inventory', 'store.manage_pricing'], superuser)
        assert group.permissions.count() == 2

    def test_unknown_permission_rejected(self, make_user):
        superuser = make_user(email='super4@example.com', is_superuser=True, is_staff=True)
        group = Group.objects.create(name='Bad Perm Test')
        with pytest.raises(ValidationError):
            services.set_role_permissions(group, ['store.not_a_real_permission'], superuser)


@pytest.mark.django_db
class TestApiEndToEnd:
    def test_full_request_approve_flow_updates_effective_permissions(
        self, api_client, regular_user, make_user, inventory_role, manager_with_full_store,
    ):
        api_client.force_authenticate(regular_user)
        resp = api_client.post(
            REQUESTS_URL,
            {'group_id': inventory_role.id, 'duration_hours': 2, 'justification': 'need to test something'},
            format='json',
        )
        assert resp.status_code == 201
        request_id = resp.data['id']

        api_client.force_authenticate(manager_with_full_store)
        resp = api_client.post(f'{REQUESTS_URL}{request_id}/approve/', {}, format='json')
        assert resp.status_code == 200

        api_client.force_authenticate(regular_user)
        resp = api_client.get(MY_PERMISSIONS_URL)
        assert 'store.manage_inventory' in resp.data['permissions']

    def test_pending_requests_only_shows_qualifying_ones(
        self, api_client, regular_user, make_user, inventory_role, full_store_role, manager_with_full_store,
    ):
        # A request for full_store_role — manager_with_full_store qualifies
        # (holds exactly that). A second manager with ONLY inventory does not
        # qualify to approve a full_store_role request.
        inventory_only_manager = make_user(email='inv-mgr@example.com')
        RoleGrant.objects.create(user=inventory_only_manager, group=inventory_role, expires_at=None)

        api_client.force_authenticate(regular_user)
        api_client.post(
            REQUESTS_URL,
            {'group_id': full_store_role.id, 'justification': 'need full access'},
            format='json',
        )

        api_client.force_authenticate(inventory_only_manager)
        resp = api_client.get(PENDING_URL)
        assert resp.data == []

        api_client.force_authenticate(manager_with_full_store)
        resp = api_client.get(PENDING_URL)
        assert len(resp.data) == 1

    def test_role_create_requires_manage_roles_permission(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        resp = api_client.post(ROLES_URL, {'name': 'New Role', 'permission_codenames': []}, format='json')
        assert resp.status_code == 403
        entry = AdminActionLog.objects.filter(action='permission_denied').latest('created')
        assert entry.actor == regular_user

    def test_superuser_can_create_role(self, api_client, make_user):
        superuser = make_user(email='super5@example.com', is_superuser=True, is_staff=True)
        api_client.force_authenticate(superuser)
        resp = api_client.post(
            ROLES_URL, {'name': 'Brand New Role', 'permission_codenames': ['store.manage_inventory']}, format='json',
        )
        assert resp.status_code == 201
        assert Group.objects.filter(name='Brand New Role').exists()

    def test_grant_list_requires_permission(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        resp = api_client.get(GRANTS_URL)
        assert resp.status_code == 403
