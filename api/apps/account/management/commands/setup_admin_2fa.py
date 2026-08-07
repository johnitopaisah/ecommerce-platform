"""
Provision (or re-provision) a confirmed TOTP device for a staff/superuser
account, printing the provisioning URI for an authenticator app.

Necessary because OTPAdminSite (config/urls.py) denies /django-admin/ access
entirely to staff users with no verified OTP device — this has to be run
BEFORE (or in the same deploy as) enabling OTPAdminSite for any account that
needs to keep admin access, or that account is locked out.

Usage:
    python manage.py setup_admin_2fa connect@johnisah.com
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()


class Command(BaseCommand):
    help = 'Provision a confirmed TOTP device for a staff/superuser account.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)

    def handle(self, *args, **options):
        email = options['email'].lower().strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'No user with email {email}')

        if not user.is_staff:
            raise CommandError(f'{email} is not a staff user — /django-admin/ access requires is_staff.')

        # Replace any existing device so re-running this is safe/idempotent —
        # old devices (and their secrets) are invalidated.
        TOTPDevice.objects.filter(user=user, name='default').delete()
        device = TOTPDevice.objects.create(user=user, name='default', confirmed=True)

        self.stdout.write(self.style.SUCCESS(f'TOTP device created for {email}'))
        self.stdout.write('')
        self.stdout.write('Scan this into an authenticator app (Google Authenticator, 1Password, Authy):')
        self.stdout.write(self.style.WARNING(device.config_url))
        self.stdout.write('')
        self.stdout.write(f'Or enter this secret key manually: {device.key}')
