"""
RBAC — role grants and the request/approval workflow around them.

Deliberately NOT a custom Role model — Django's built-in `Group` (already
available for free via UserBase's PermissionsMixin) IS the role. A role's
*definition* is just a Group's attached Permissions, managed through the
normal Django auth tables. What's missing from Django's built-in system,
and what this app adds, is *time-bounded* group membership and the
request/approval workflow around granting it — see apps.rbac.permissions
for how a grant's validity actually gets resolved and enforced.
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class RoleGrant(models.Model):
    """
    A role (Group) actually held by a user, permanent or time-bounded.
    This — not Django's raw `user.groups` — is the source of truth for
    "does this user currently hold this role": a row here can be revoked
    or can lapse past `expires_at` without ever touching `user.groups`
    directly, which keeps effective-permission resolution ("is this grant
    live right now") a pure function of this table rather than requiring
    a sweep job to keep group membership in sync with time.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        REVOKED = 'revoked', _('Revoked')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='role_grants',
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        Group,
        related_name='role_grants',
        on_delete=models.CASCADE,
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='granted_role_grants',
        on_delete=models.SET_NULL,
        null=True,
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text=_('Null = permanent grant.'),
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True,
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='revoked_role_grants',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Role grant'
        verbose_name_plural = 'Role grants'
        ordering = ('-granted_at',)
        permissions = [
            ('manage_roles', 'Can define/edit role permission sets'),
            ('grant_roles', 'Can grant or approve role assignments for other users'),
        ]

    @property
    def is_currently_valid(self) -> bool:
        """Live right now — status is ACTIVE and (permanent or not yet expired)."""
        if self.status != self.Status.ACTIVE:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True

    def revoke(self, by_user):
        self.status = self.Status.REVOKED
        self.revoked_by = by_user
        self.revoked_at = timezone.now()
        self.save(update_fields=['status', 'revoked_by', 'revoked_at'])

    def __str__(self):
        return f'{self.user} — {self.group.name}'


class RoleGrantRequest(models.Model):
    """
    Self-service "grant me this role for this long, because" request.
    Approval is enforced entirely in apps.rbac.services — this model is
    just the record of the workflow, not where the security rule lives.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        DENIED = 'denied', _('Denied')
        CANCELLED = 'cancelled', _('Cancelled')

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='role_requests',
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        Group,
        related_name='role_requests',
        on_delete=models.CASCADE,
    )
    duration_hours = models.PositiveIntegerField(
        null=True, blank=True,
        help_text=_('Null = permanent grant requested.'),
    )
    justification = models.TextField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='reviewed_role_requests',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.CharField(max_length=255, blank=True)
    resulting_grant = models.OneToOneField(
        RoleGrant,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='source_request',
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Role grant request'
        verbose_name_plural = 'Role grant requests'
        ordering = ('-created',)

    def __str__(self):
        return f'{self.requester} requests {self.group.name} ({self.status})'
