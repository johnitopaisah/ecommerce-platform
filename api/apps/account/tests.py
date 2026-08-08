"""
Auth flow tests — registration, login, activation, password reset,
resend-activation, and the throttling added during the security hardening
pass. These are the highest blast-radius endpoints in the API (every one is
AllowAny and pre-authentication), so they're covered first.
"""

from unittest.mock import patch

import pytest
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import UserBase
from .tokens import account_activation_token

REGISTER_URL = '/api/v1/auth/register/'
LOGIN_URL = '/api/v1/auth/token/'
RESEND_ACTIVATION_URL = '/api/v1/auth/activate/resend/'
PASSWORD_RESET_URL = '/api/v1/auth/password-reset/'
PASSWORD_RESET_CONFIRM_URL = '/api/v1/auth/password-reset/confirm/'


def _register_payload(**overrides):
    payload = {
        'email': 'newuser@example.com',
        'user_name': 'newuser',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'CorrectHorse9!Battery',
        'password2': 'CorrectHorse9!Battery',
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_inactive_user_and_sends_activation_email(self, api_client):
        response = api_client.post(REGISTER_URL, _register_payload(), format='json')

        assert response.status_code == 201
        user = UserBase.objects.get(email='newuser@example.com')
        assert user.is_active is False
        assert len(mail.outbox) == 1
        assert 'activate' in mail.outbox[0].subject.lower()

    def test_register_rejects_duplicate_email(self, api_client, make_user):
        make_user(email='taken@example.com')
        response = api_client.post(
            REGISTER_URL, _register_payload(email='taken@example.com', user_name='other'), format='json'
        )
        assert response.status_code == 400
        assert 'email' in response.data['errors']

    def test_register_rejects_mismatched_passwords(self, api_client):
        response = api_client.post(
            REGISTER_URL, _register_payload(password2='SomethingElse9!'), format='json'
        )
        assert response.status_code == 400

    def test_register_rejects_short_password(self, api_client):
        # MinimumLengthValidator raised to 10 chars during the hardening pass
        response = api_client.post(
            REGISTER_URL, _register_payload(password='short1!', password2='short1!'), format='json'
        )
        assert response.status_code == 400

    def test_register_is_throttled(self, api_client):
        # DEFAULT_THROTTLE_RATES['auth_register'] = '5/hour'
        for i in range(5):
            resp = api_client.post(
                REGISTER_URL,
                _register_payload(email=f'user{i}@example.com', user_name=f'user{i}'),
                format='json',
            )
            assert resp.status_code == 201

        resp = api_client.post(
            REGISTER_URL, _register_payload(email='oneMore@example.com', user_name='onemore'), format='json'
        )
        assert resp.status_code == 429


@pytest.mark.django_db
class TestLogin:
    def test_login_succeeds_for_active_user(self, api_client, make_user):
        make_user(email='active@example.com', password='CorrectHorse9!Battery')
        response = api_client.post(
            LOGIN_URL,
            {'email': 'active@example.com', 'password': 'CorrectHorse9!Battery'},
            format='json',
        )
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_rejects_inactive_user(self, api_client, make_user):
        make_user(email='unverified@example.com', password='CorrectHorse9!Battery', is_active=False)
        response = api_client.post(
            LOGIN_URL,
            {'email': 'unverified@example.com', 'password': 'CorrectHorse9!Battery'},
            format='json',
        )
        # SimpleJWT + Django's ModelBackend both refuse inactive users —
        # generic 401, not a "your account isn't active" leak.
        assert response.status_code == 401

    def test_login_rejects_wrong_password(self, api_client, make_user):
        make_user(email='active2@example.com', password='CorrectHorse9!Battery')
        response = api_client.post(
            LOGIN_URL,
            {'email': 'active2@example.com', 'password': 'WrongPassword!'},
            format='json',
        )
        assert response.status_code == 401

    def test_login_is_throttled(self, api_client, make_user):
        # DEFAULT_THROTTLE_RATES['auth_login'] = '10/minute'
        make_user(email='bruteforced@example.com', password='CorrectHorse9!Battery')
        for _ in range(10):
            api_client.post(
                LOGIN_URL,
                {'email': 'bruteforced@example.com', 'password': 'wrong'},
                format='json',
            )
        response = api_client.post(
            LOGIN_URL,
            {'email': 'bruteforced@example.com', 'password': 'wrong'},
            format='json',
        )
        assert response.status_code == 429


@pytest.mark.django_db
class TestActivation:
    def test_activate_with_valid_token_activates_and_redirects(self, api_client, make_user):
        user = make_user(email='pending@example.com', is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        response = api_client.get(f'/api/v1/auth/activate/{uid}/{token}/')

        assert response.status_code == 302
        assert '/activated' in response.url
        user.refresh_from_db()
        assert user.is_active is True

    def test_activate_with_invalid_token_redirects_to_failure(self, api_client, make_user):
        user = make_user(email='pending2@example.com', is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = api_client.get(f'/api/v1/auth/activate/{uid}/not-a-real-token/')

        assert response.status_code == 302
        assert '/activation-failed' in response.url
        user.refresh_from_db()
        assert user.is_active is False

    def test_activation_token_is_single_use(self, api_client, make_user):
        # AccountActivationTokenGenerator bakes is_active into the hash, so
        # the same link can't activate a second time once is_active flips.
        user = make_user(email='oncetoken@example.com', is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        first = api_client.get(f'/api/v1/auth/activate/{uid}/{token}/')
        second = api_client.get(f'/api/v1/auth/activate/{uid}/{token}/')

        assert '/activated' in first.url
        assert '/activation-failed' in second.url


@pytest.mark.django_db
class TestResendActivation:
    def test_resend_activation_sends_email_for_pending_account(self, api_client, make_user):
        make_user(email='pending3@example.com', is_active=False)
        response = api_client.post(RESEND_ACTIVATION_URL, {'email': 'pending3@example.com'}, format='json')

        assert response.status_code == 200
        assert len(mail.outbox) == 1

    def test_resend_activation_does_not_leak_account_existence(self, api_client, make_user):
        make_user(email='alreadyactive@example.com', is_active=True)

        resp_nonexistent = api_client.post(RESEND_ACTIVATION_URL, {'email': 'nobody@example.com'}, format='json')
        resp_already_active = api_client.post(
            RESEND_ACTIVATION_URL, {'email': 'alreadyactive@example.com'}, format='json'
        )

        assert resp_nonexistent.status_code == resp_already_active.status_code == 200
        assert resp_nonexistent.data == resp_already_active.data
        assert len(mail.outbox) == 0  # neither case should have sent anything


@pytest.mark.django_db
class TestPasswordReset:
    def test_password_reset_request_does_not_leak_account_existence(self, api_client, make_user):
        make_user(email='exists@example.com')

        resp_exists = api_client.post(PASSWORD_RESET_URL, {'email': 'exists@example.com'}, format='json')
        resp_missing = api_client.post(PASSWORD_RESET_URL, {'email': 'nobody@example.com'}, format='json')

        assert resp_exists.status_code == resp_missing.status_code == 200
        assert resp_exists.data == resp_missing.data
        assert len(mail.outbox) == 1  # only the real account actually got an email

    def test_password_reset_confirm_with_valid_token(self, api_client, make_user):
        from django.contrib.auth.tokens import default_token_generator

        user = make_user(email='resetme@example.com', password='OldPassword9!')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = api_client.post(
            PASSWORD_RESET_CONFIRM_URL,
            {
                'uid': uid, 'token': token,
                'new_password': 'BrandNewPassw0rd!', 'new_password2': 'BrandNewPassw0rd!',
            },
            format='json',
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password('BrandNewPassw0rd!')

    def test_password_reset_confirm_with_invalid_token(self, api_client, make_user):
        user = make_user(email='resetme2@example.com', password='OldPassword9!')
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = api_client.post(
            PASSWORD_RESET_CONFIRM_URL,
            {
                'uid': uid, 'token': 'garbage-token',
                'new_password': 'BrandNewPassw0rd!', 'new_password2': 'BrandNewPassw0rd!',
            },
            format='json',
        )

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password('OldPassword9!')  # unchanged


CUSTOMERS_URL = '/api/v1/admin/customers/'
TEAM_URL = '/api/v1/admin/team/'


@pytest.fixture
def manage_staff_user(make_user):
    """A user with exactly account.manage_staff — not a superuser — to
    exercise the real permission check rather than the superuser bypass."""
    from django.contrib.auth.models import Group, Permission
    from apps.rbac.models import RoleGrant

    user = make_user(email='hr@example.com', is_staff=True)
    group = Group.objects.create(name='Team Provisioner Test')
    group.permissions.add(
        Permission.objects.get(codename='manage_staff', content_type__app_label='account')
    )
    RoleGrant.objects.create(user=user, group=group, expires_at=None)
    return user


@pytest.mark.django_db
class TestCustomerVsTeamSplit:
    def test_customer_list_excludes_staff(self, api_client, staff_user, make_user):
        customer = make_user(email='shopper2@example.com')
        api_client.force_authenticate(staff_user)

        response = api_client.get(CUSTOMERS_URL)

        emails = [u['email'] for u in response.data]
        assert customer.email in emails
        assert staff_user.email not in emails

    def test_team_list_excludes_customers(self, api_client, staff_user, make_user):
        customer = make_user(email='shopper3@example.com')
        api_client.force_authenticate(staff_user)

        response = api_client.get(TEAM_URL)

        emails = [u['email'] for u in response.data]
        assert staff_user.email in emails
        assert customer.email not in emails

    def test_team_list_shows_active_role_badges(self, api_client, staff_user, manage_staff_user):
        api_client.force_authenticate(staff_user)

        response = api_client.get(TEAM_URL)

        entry = next(u for u in response.data if u['email'] == manage_staff_user.email)
        assert entry['roles'][0]['group_name'] == 'Team Provisioner Test'

    def test_regular_customer_cannot_view_team_list(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        response = api_client.get(TEAM_URL)
        assert response.status_code == 403


@pytest.mark.django_db
class TestCreateTeamMember:
    def test_requires_manage_staff_not_just_manage_users(self, api_client, make_user):
        from django.contrib.auth.models import Group, Permission
        from apps.rbac.models import RoleGrant

        support_only = make_user(email='support-only@example.com')
        group = Group.objects.create(name='Support Only Test')
        group.permissions.add(
            Permission.objects.get(codename='manage_users', content_type__app_label='account')
        )
        RoleGrant.objects.create(user=support_only, group=group, expires_at=None)
        api_client.force_authenticate(support_only)

        response = api_client.post(
            TEAM_URL, {'email': 'newhire@example.com', 'user_name': 'newhire'}, format='json',
        )

        assert response.status_code == 403

    def test_qualified_user_can_create_team_member(self, api_client, manage_staff_user):
        api_client.force_authenticate(manage_staff_user)

        response = api_client.post(
            TEAM_URL,
            {'email': 'newhire2@example.com', 'user_name': 'newhire2', 'first_name': 'New'},
            format='json',
        )

        assert response.status_code == 201
        user = UserBase.objects.get(email='newhire2@example.com')
        assert user.is_staff is True
        assert user.is_active is True
        assert user.has_usable_password() is False

    def test_created_team_member_receives_password_set_email(self, api_client, manage_staff_user):
        api_client.force_authenticate(manage_staff_user)

        api_client.post(
            TEAM_URL, {'email': 'newhire3@example.com', 'user_name': 'newhire3'}, format='json',
        )

        assert len(mail.outbox) == 1
        assert 'reset-password' in mail.outbox[0].body

    def test_duplicate_email_rejected(self, api_client, manage_staff_user, staff_user):
        api_client.force_authenticate(manage_staff_user)

        response = api_client.post(
            TEAM_URL, {'email': staff_user.email, 'user_name': 'someoneelse'}, format='json',
        )

        assert response.status_code == 400

    def test_initial_role_granted_only_if_subset_of_creators_permissions(
        self, api_client, manage_staff_user,
    ):
        from django.contrib.auth.models import Group, Permission

        broader_group = Group.objects.create(name='Broader Than Creator')
        broader_group.permissions.add(
            Permission.objects.get(codename='manage_staff', content_type__app_label='account'),
            Permission.objects.get(codename='view_dashboard', content_type__app_label='core'),
        )
        api_client.force_authenticate(manage_staff_user)

        response = api_client.post(
            TEAM_URL,
            {
                'email': 'newhire4@example.com', 'user_name': 'newhire4',
                'initial_group_id': broader_group.id,
            },
            format='json',
        )

        # manage_staff_user only holds manage_staff — broader_group also
        # grants view_dashboard, which isn't a subset of what they hold.
        assert response.status_code == 403
        assert not UserBase.objects.filter(email='newhire4@example.com').exists()

    def test_initial_role_granted_when_within_creators_permissions(
        self, api_client, manage_staff_user,
    ):
        from django.contrib.auth.models import Group, Permission
        from apps.rbac.models import RoleGrant

        narrow_group = Group.objects.create(name='Narrow Test')
        narrow_group.permissions.add(
            Permission.objects.get(codename='manage_staff', content_type__app_label='account')
        )
        api_client.force_authenticate(manage_staff_user)

        response = api_client.post(
            TEAM_URL,
            {
                'email': 'newhire5@example.com', 'user_name': 'newhire5',
                'initial_group_id': narrow_group.id, 'duration_hours': 4,
            },
            format='json',
        )

        assert response.status_code == 201
        user = UserBase.objects.get(email='newhire5@example.com')
        grant = RoleGrant.objects.get(user=user)
        assert grant.group == narrow_group
        assert grant.expires_at is not None
        assert grant.granted_by == manage_staff_user
