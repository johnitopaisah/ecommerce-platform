"""
Core permission-resolution tests — this module is the foundation everything
else in RBAC depends on, so it gets tested precisely: union-of-grants
correctness, temporary-grant expiry, revocation, superuser bypass, and that
denials actually get logged (the whole point of building this layer).
"""

from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.core.models import AdminActionLog
from .models import RoleGrant
from .permissions import RequiresPermission, get_effective_permissions, user_has_permission

CODENAME = 'store.manage_inventory'


@pytest.fixture
def permission(db):
    return Permission.objects.get(codename='manage_inventory', content_type__app_label='store')


@pytest.fixture
def group_with_permission(db, permission):
    group = Group.objects.create(name='Test Inventory Role')
    group.permissions.add(permission)
    return group


@pytest.mark.django_db
class TestGetEffectivePermissions:
    def test_anonymous_user_has_no_permissions(self):
        from django.contrib.auth.models import AnonymousUser
        assert get_effective_permissions(AnonymousUser()) == set()

    def test_user_with_no_grants_has_no_permissions(self, regular_user):
        assert get_effective_permissions(regular_user) == set()

    def test_active_permanent_grant_is_included(self, regular_user, group_with_permission):
        RoleGrant.objects.create(user=regular_user, group=group_with_permission, expires_at=None)
        assert CODENAME in get_effective_permissions(regular_user)

    def test_active_unexpired_temporary_grant_is_included(self, regular_user, group_with_permission):
        RoleGrant.objects.create(
            user=regular_user, group=group_with_permission,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        assert CODENAME in get_effective_permissions(regular_user)

    def test_expired_temporary_grant_is_excluded(self, regular_user, group_with_permission):
        RoleGrant.objects.create(
            user=regular_user, group=group_with_permission,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        assert CODENAME not in get_effective_permissions(regular_user)

    def test_revoked_grant_is_excluded_even_if_not_yet_expired(self, regular_user, group_with_permission):
        grant = RoleGrant.objects.create(
            user=regular_user, group=group_with_permission,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        grant.revoke(by_user=regular_user)
        assert CODENAME not in get_effective_permissions(regular_user)

    def test_permissions_from_multiple_grants_are_unioned(self, regular_user, db):
        perm_a = Permission.objects.get(codename='manage_inventory', content_type__app_label='store')
        perm_b = Permission.objects.get(codename='manage_pricing', content_type__app_label='store')
        group_a = Group.objects.create(name='A')
        group_a.permissions.add(perm_a)
        group_b = Group.objects.create(name='B')
        group_b.permissions.add(perm_b)
        RoleGrant.objects.create(user=regular_user, group=group_a, expires_at=None)
        RoleGrant.objects.create(user=regular_user, group=group_b, expires_at=None)

        effective = get_effective_permissions(regular_user)

        assert 'store.manage_inventory' in effective
        assert 'store.manage_pricing' in effective


@pytest.mark.django_db
class TestUserHasPermission:
    def test_superuser_bypasses_grants_entirely(self, make_user):
        superuser = make_user(email='super@example.com', is_superuser=True, is_staff=True)
        assert user_has_permission(superuser, 'anything.not_a_real_permission') is True

    def test_unauthenticated_never_has_permission(self):
        from django.contrib.auth.models import AnonymousUser
        assert user_has_permission(AnonymousUser(), CODENAME) is False

    def test_user_without_grant_lacks_permission(self, regular_user):
        assert user_has_permission(regular_user, CODENAME) is False

    def test_user_with_grant_has_permission(self, regular_user, group_with_permission):
        RoleGrant.objects.create(user=regular_user, group=group_with_permission, expires_at=None)
        assert user_has_permission(regular_user, CODENAME) is True

    def test_requires_all_of_multiple_codenames(self, regular_user, group_with_permission):
        # Grant only gives manage_inventory — asking for that AND something
        # else it doesn't have should fail (AND semantics, not OR).
        RoleGrant.objects.create(user=regular_user, group=group_with_permission, expires_at=None)
        assert user_has_permission(regular_user, CODENAME, 'store.manage_pricing') is False


@pytest.mark.django_db
class TestRequiresPermission:
    def _request(self, user, method='GET', path='/api/v1/admin/products/'):
        factory = APIRequestFactory()
        raw = getattr(factory, method.lower())(path)
        request = Request(raw)
        request.user = user
        return request

    def test_denies_and_logs_when_permission_missing(self, regular_user):
        permission_class = RequiresPermission(CODENAME)()
        request = self._request(regular_user)

        result = permission_class.has_permission(request, None)

        assert result is False
        entry = AdminActionLog.objects.filter(action='permission_denied').latest('created')
        assert entry.outcome == AdminActionLog.Outcome.DENIED
        assert entry.actor == regular_user
        assert entry.detail['required_permissions'] == [CODENAME]

    def test_grants_without_logging_when_permission_present(self, regular_user, group_with_permission):
        RoleGrant.objects.create(user=regular_user, group=group_with_permission, expires_at=None)
        permission_class = RequiresPermission(CODENAME)()
        request = self._request(regular_user)

        result = permission_class.has_permission(request, None)

        assert result is True
        assert not AdminActionLog.objects.filter(action='permission_denied').exists()

    def test_superuser_always_granted(self, make_user):
        superuser = make_user(email='super2@example.com', is_superuser=True, is_staff=True)
        permission_class = RequiresPermission(CODENAME)()
        request = self._request(superuser)

        assert permission_class.has_permission(request, None) is True
