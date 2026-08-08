"""
Create/update the standard role taxonomy as Django Groups with their
permission sets attached. Safe to re-run any time a role's permission set
changes — each role's permissions are fully replaced (via .set()) to match
this definition, not merely added to, so this file is the single source of
truth for "what does this role grant" rather than an append-only history.

"Super Admin" is deliberately NOT a Group here — it maps directly to
Django's built-in `is_superuser=True`, which apps.rbac.permissions already
treats as an unconditional bypass. Creating a Group for it would just be a
second, redundant way to express the same thing.

Usage:
    python manage.py seed_roles
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Each value is a list of (app_label, codename) pairs. Codenames without an
# app_label prefix here are Django's auto-generated per-model CRUD ones
# (add_x/change_x/delete_x/view_x); the custom action-level ones (e.g.
# advance_status, manage_inventory) were defined via Meta.permissions on
# their respective models — see apps/{store,orders,account,core,rbac}/models.py.
ROLE_DEFINITIONS: dict[str, list[tuple[str, str]]] = {
    # ── Business operations ─────────────────────────────────────────────
    'Store Manager': [
        ('store', 'add_product'), ('store', 'change_product'),
        ('store', 'delete_product'), ('store', 'view_product'),
        ('store', 'manage_inventory'), ('store', 'manage_pricing'),
        ('store', 'add_category'), ('store', 'change_category'),
        ('store', 'delete_category'), ('store', 'view_category'),
    ],
    # Flagged as an open question during design (real headcount, or
    # premature subdivision of Store Manager?) — seeded anyway so the
    # option exists; delete the Group later if it never gets used.
    'Inventory Manager': [
        ('store', 'view_product'), ('store', 'manage_inventory'),
    ],
    'Order Fulfillment': [
        ('orders', 'view_order'), ('orders', 'advance_status'),
    ],
    'Customer Support': [
        ('orders', 'view_order'), ('orders', 'refund_partial'),
        ('account', 'view_userbase'),
    ],
    'Marketing': [
        ('coupons', 'add_coupon'), ('coupons', 'change_coupon'),
        ('coupons', 'delete_coupon'), ('coupons', 'view_coupon'),
    ],
    'Finance': [
        ('orders', 'view_order'), ('orders', 'refund_full'),
        ('orders', 'refund_partial'), ('payment', 'view_payment'),
    ],
    'Content Moderator': [
        ('store', 'view_review'), ('store', 'moderate_reviews'),
    ],
    'Auditor': [
        ('store', 'view_product'), ('store', 'view_category'), ('store', 'view_review'),
        ('orders', 'view_order'), ('coupons', 'view_coupon'),
        ('account', 'view_userbase'), ('core', 'view_audit_log'),
    ],
    # ── Platform / engineering ──────────────────────────────────────────
    # Broad read access + audit visibility, deliberately no write access —
    # a developer being able to casually edit live orders or issue refunds
    # is a liability, not a convenience. Same shape as Auditor right now;
    # kept as a separate Group because the two are organizationally
    # distinct even where the permission set currently overlaps.
    'Developer': [
        ('store', 'view_product'), ('store', 'view_category'), ('store', 'view_review'),
        ('orders', 'view_order'), ('coupons', 'view_coupon'),
        ('account', 'view_userbase'), ('core', 'view_audit_log'),
    ],
    # Deliberately minimal (read-only) until the QA-needs-write-access
    # question is resolved — see the design notes: that ask looked more
    # like "there's no staging environment" than a permissions problem,
    # and granting broad production write access to solve a testing gap
    # is the wrong layer to solve it at. Widen this only as a deliberate
    # decision, not a default.
    'QA': [
        ('store', 'view_product'), ('orders', 'view_order'), ('coupons', 'view_coupon'),
    ],
    'IT / Platform Ops': [
        ('account', 'manage_users'), ('account', 'revoke_sessions'),
        ('account', 'view_userbase'), ('rbac', 'grant_roles'),
    ],
    'Security / Compliance': [
        ('core', 'view_audit_log'), ('account', 'revoke_sessions'),
        ('account', 'view_userbase'),
    ],
}


class Command(BaseCommand):
    help = 'Create/update the standard RBAC role taxonomy as Django Groups.'

    def handle(self, *args, **options):
        for role_name, perm_pairs in ROLE_DEFINITIONS.items():
            group, created = Group.objects.get_or_create(name=role_name)

            permissions = []
            missing = []
            for app_label, codename in perm_pairs:
                try:
                    permissions.append(
                        Permission.objects.get(content_type__app_label=app_label, codename=codename)
                    )
                except Permission.DoesNotExist:
                    missing.append(f'{app_label}.{codename}')

            group.permissions.set(permissions)

            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'{verb} "{role_name}" — {len(permissions)} permissions')
            if missing:
                self.stderr.write(
                    self.style.WARNING(f'  Missing (not found, skipped): {", ".join(missing)}')
                )

        self.stdout.write(self.style.SUCCESS(f'\nSeeded {len(ROLE_DEFINITIONS)} roles.'))
