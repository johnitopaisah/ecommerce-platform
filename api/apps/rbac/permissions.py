"""
The core permission-checking module — the "clean, service-boundary-ready"
layer every domain app (store/orders/coupons/payment/basket/account) should
depend on for authorization, instead of reaching into RoleGrant or Group
directly. This is the boundary that makes "extract this into its own
service later" realistic rather than aspirational.

Deliberately does NOT embed permissions into JWTs. A token here is only
ever proof of identity, never proof of authorization — effective
permissions are recomputed from the database on every permission-checked
request. Given this project's actual traffic (an admin panel, not the
public storefront hot path), one extra query per admin request is a
non-issue, and it fully avoids the staleness problem that plagues
JWT-embedded claims: SimpleJWT's refresh-token rotation copies claims from
the *old* token rather than recomputing them, so a claim baked in at login
would silently outlive a since-revoked or since-expired grant until the
refresh token itself expired — up to 7 days in this project's config, not
an acceptable window for something explicitly designed to expire on time.
"""

from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import BasePermission

from .models import RoleGrant


def get_effective_permissions(user) -> set[str]:
    """
    Return {"app_label.codename", ...} for every permission the user
    currently holds through an active, unexpired role grant.

    Superusers are deliberately NOT special-cased here — this stays a
    precise, testable "what do their grants actually say" query. Callers
    (user_has_permission / RequiresPermission) handle the superuser bypass.
    """
    if not user or not user.is_authenticated:
        return set()

    grants = (
        RoleGrant.objects
        .filter(user=user, status=RoleGrant.Status.ACTIVE)
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
        .prefetch_related('group__permissions__content_type')
    )
    perms = set()
    for grant in grants:
        for p in grant.group.permissions.all():
            perms.add(f'{p.content_type.app_label}.{p.codename}')
    return perms


def user_has_permission(user, *codenames: str) -> bool:
    """True if the user holds every one of the given 'app_label.codename' permissions."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    effective = get_effective_permissions(user)
    return all(c in effective for c in codenames)


def RequiresPermission(*codenames: str):
    """
    DRF permission-class factory.

        permission_classes = [RequiresPermission('orders.advance_status')]

    Multiple codenames require ALL of them (AND). Denials are logged
    automatically — that's the coverage gap that mattered (see the audit
    logging design notes): nothing today catches "someone tried an action
    they weren't allowed to." Grants on state-changing requests are still
    expected to be logged by the view itself with real business context
    (e.g. "Order #ABC123"), same as the existing log_admin_action pattern —
    this layer's job is denials, not duplicating what views already do.
    """
    class _RequiresPermission(BasePermission):
        def has_permission(self, request, view):
            granted = user_has_permission(request.user, *codenames)
            if not granted:
                _log_denial(request, codenames)
            return granted

    return _RequiresPermission


def _log_denial(request, codenames):
    from apps.core.audit import log_admin_action
    from apps.core.models import AdminActionLog

    log_admin_action(
        request,
        action='permission_denied',
        target=f'{request.method} {request.path}',
        detail={'required_permissions': list(codenames)},
        outcome=AdminActionLog.Outcome.DENIED,
    )


def require_permission(request, *codenames: str):
    """
    Imperative-style check for inside a view body — needed wherever a
    single function-based view handles multiple HTTP methods that each
    require a *different* permission (DRF's @permission_classes applies
    one check to the whole view, method-agnostic, which doesn't fit e.g.
    "GET needs view_product, POST needs add_product" on the same
    function). Raises PermissionDenied (auto-logged, same as
    RequiresPermission) if the requirement isn't met.
    """
    if not user_has_permission(request.user, *codenames):
        _log_denial(request, codenames)
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(f"Requires: {', '.join(codenames)}")
