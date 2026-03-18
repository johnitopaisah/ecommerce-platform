"""
Custom user model.

Changes from the original monolith:
- Added `last_name` (was missing)
- `phone_number` kept as CharField with basic validation in the serializer
- Address fields kept flat on the user for simplicity at this stage
- `is_active` defaults to False — user must activate via email link
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


class CustomAccountManager(BaseUserManager):

    def create_user(self, email, user_name, password, **extra_fields):
        if not email:
            raise ValueError(_('An email address is required.'))
        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, user_name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, user_name, password, **extra_fields)


class UserBase(AbstractBaseUser, PermissionsMixin):
    """Central user model for the platform."""

    email = models.EmailField(_('email address'), unique=True)
    user_name = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    about = models.TextField(_('about'), max_length=500, blank=True)

    # Delivery / billing address
    country = CountryField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    postcode = models.CharField(max_length=12, blank=True)
    address_line_1 = models.CharField(max_length=150, blank=True)
    address_line_2 = models.CharField(max_length=150, blank=True)
    town_city = models.CharField(max_length=150, blank=True)

    # Status flags
    is_active = models.BooleanField(
        default=False,
        help_text=_('User must activate their account via email.'),
    )
    is_staff = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = CustomAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return self.email
