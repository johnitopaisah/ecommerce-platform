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
