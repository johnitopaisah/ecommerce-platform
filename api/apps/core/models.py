from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AdminActionLog(models.Model):
    """
    Audit trail for sensitive staff-initiated actions (price changes, order
    status changes, refunds, account deactivation) — "who changed what",
    flagged as a gap during the auth/authorization hardening pass.
    Append-only: nothing here is ever edited or deleted by the application.

    `outcome` defaults to SUCCESS for backward compatibility with every
    existing call site (which only ever logged after a successful action).
    The RBAC permission-checking module (apps.rbac.permissions) is the only
    place that logs DENIED — that's the signal a plain "who changed what"
    log misses: someone repeatedly probing for access they don't have.
    """
    class Outcome(models.TextChoices):
        SUCCESS = 'success', _('Success')
        DENIED = 'denied', _('Denied')
        ERROR = 'error', _('Error')

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions',
    )
    action = models.CharField(max_length=100, db_index=True)
    target = models.CharField(max_length=255, help_text='e.g. "Order #ABC123", "Product: T-Shirt"')
    outcome = models.CharField(
        max_length=10, choices=Outcome.choices, default=Outcome.SUCCESS, db_index=True,
    )
    detail = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Admin action log'
        verbose_name_plural = 'Admin action logs'
        permissions = [
            ('view_audit_log', 'Can view the audit log'),
            ('view_dashboard', 'Can view the admin dashboard overview/stats'),
        ]

    def __str__(self):
        return f'{self.actor} — {self.action} — {self.target} ({self.created:%Y-%m-%d %H:%M})'
