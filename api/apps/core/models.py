from django.conf import settings
from django.db import models


class AdminActionLog(models.Model):
    """
    Audit trail for sensitive staff-initiated actions (price changes, order
    status changes, refunds, account deactivation) — "who changed what",
    flagged as a gap during the auth/authorization hardening pass.
    Append-only: nothing here is ever edited or deleted by the application.
    """
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions',
    )
    action = models.CharField(max_length=100, db_index=True)
    target = models.CharField(max_length=255, help_text='e.g. "Order #ABC123", "Product: T-Shirt"')
    detail = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Admin action log'
        verbose_name_plural = 'Admin action logs'

    def __str__(self):
        return f'{self.actor} — {self.action} — {self.target} ({self.created:%Y-%m-%d %H:%M})'
