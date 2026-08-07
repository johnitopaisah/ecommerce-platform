"""
Payment endpoint tests — focused on the webhook's signature verification,
since that's the entire security boundary for an endpoint that has no auth
of its own by design (Stripe can't send a JWT). Also covers create-intent's
auth requirement.
"""

from unittest.mock import patch, MagicMock

import pytest
import stripe

WEBHOOK_URL = '/api/v1/payment/webhook/'
CREATE_INTENT_URL = '/api/v1/payment/create-intent/'


@pytest.mark.django_db
class TestStripeWebhook:
    @patch('apps.payment.views.stripe.Webhook.construct_event')
    def test_webhook_rejects_invalid_signature(self, mock_construct, api_client):
        mock_construct.side_effect = stripe.error.SignatureVerificationError('bad sig', 'sig_header')

        response = api_client.post(
            WEBHOOK_URL, data='{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='not-a-real-signature',
        )

        assert response.status_code == 400

    @patch('apps.payment.views.stripe.Webhook.construct_event')
    def test_webhook_rejects_malformed_payload(self, mock_construct, api_client):
        mock_construct.side_effect = ValueError('invalid JSON')

        response = api_client.post(
            WEBHOOK_URL, data='not-json', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='whatever',
        )

        assert response.status_code == 400

    @patch('apps.payment.views._handle_payment_succeeded')
    @patch('apps.payment.views.stripe.Webhook.construct_event')
    def test_webhook_dispatches_payment_succeeded(self, mock_construct, mock_handler, api_client):
        mock_construct.return_value = {
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_123', 'client_secret': 'secret_123'}},
        }

        response = api_client.post(
            WEBHOOK_URL, data='{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid-because-mocked',
        )

        assert response.status_code == 200
        mock_handler.assert_called_once()

    @patch('apps.payment.views._handle_payment_failed')
    @patch('apps.payment.views.stripe.Webhook.construct_event')
    def test_webhook_dispatches_payment_failed(self, mock_construct, mock_handler, api_client):
        mock_construct.return_value = {
            'type': 'payment_intent.payment_failed',
            'data': {'object': {'id': 'pi_456', 'client_secret': 'secret_456'}},
        }

        response = api_client.post(
            WEBHOOK_URL, data='{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid-because-mocked',
        )

        assert response.status_code == 200
        mock_handler.assert_called_once()

    @patch('apps.payment.views.stripe.Webhook.construct_event')
    def test_webhook_ignores_unhandled_event_types(self, mock_construct, api_client):
        mock_construct.return_value = {
            'type': 'charge.refunded',
            'data': {'object': {}},
        }

        response = api_client.post(
            WEBHOOK_URL, data='{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid-because-mocked',
        )

        # Unhandled types still 200 — Stripe retries on non-2xx, and we
        # deliberately don't subscribe to more than the two events we handle.
        assert response.status_code == 200


@pytest.mark.django_db
class TestCreatePaymentIntent:
    def test_requires_authentication(self, api_client):
        response = api_client.post(CREATE_INTENT_URL, {}, format='json')
        assert response.status_code == 401
