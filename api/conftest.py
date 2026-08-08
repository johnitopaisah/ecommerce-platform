"""
Shared pytest fixtures.
"""

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.account.models import UserBase


@pytest.fixture(autouse=True)
def _clear_cache():
    """
    DRF throttles store their counters in Django's cache (django-redis here).
    Without this, one test tripping a rate limit (e.g. hitting /register/
    five times) leaks state into every other test that hits the same view.
    """
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make_user(email='user@example.com', password='Sup3rSecret!42', **kwargs):
        kwargs.setdefault('user_name', email.split('@')[0])
        kwargs.setdefault('is_active', True)
        user = UserBase(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user
    return _make_user


@pytest.fixture
def regular_user(make_user):
    return make_user(email='shopper@example.com')


@pytest.fixture
def staff_user(make_user):
    """
    'Can do any admin thing' test actor — is_superuser, not just is_staff.
    Since RBAC (apps.rbac) replaced the old blanket is_staff-only IsAdminUser
    check, is_staff alone no longer grants any admin action; it only gates
    "is this an internal account" (admin-ui login, Django's own
    /django-admin/). Every existing test across the suite was written
    assuming staff_user could perform any admin action — is_superuser
    preserves that without rewriting every call site, and it's also
    literally correct: superuser is this system's "Super Admin" role (see
    apps.rbac.permissions — no Group needed for it, it's an unconditional
    bypass). Granular, non-superuser permission enforcement has its own
    dedicated coverage in apps/rbac/test_workflow.py.
    """
    return make_user(email='staff@example.com', is_staff=True, is_superuser=True)
