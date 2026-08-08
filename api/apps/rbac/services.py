"""
RBAC business logic — the request/approve/deny/revoke workflow around
RoleGrant and RoleGrantRequest. Kept separate from views.py so the rules
(especially the delegated-approval subset check) are unit-testable without
going through HTTP, and so admin-ui's future endpoints and any other
caller share exactly one implementation of "can this user approve this."
"""

from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import RoleGrant, RoleGrantRequest
from .permissions import get_effective_permissions


def group_permission_codenames(group: Group) -> set[str]:
    return {
        f'{p.content_type.app_label}.{p.codename}'
        for p in group.permissions.select_related('content_type').all()
    }


def can_manage_role(user, group: Group) -> bool:
    """
    The delegated-approval security rule: a user may grant/approve a role
    if and only if that role's entire permission set is already a subset
    of their own current effective permissions. You can only delegate
    authority you actually hold — no hierarchy table, no seniority
    concept, just set comparison. Superusers always qualify.
    """
    if user.is_superuser:
        return True
    required = group_permission_codenames(group)
    if not required:
        # A role that grants nothing meaningful — anyone can hand it out.
        return True
    return required.issubset(get_effective_permissions(user))


def request_role(requester, group: Group, duration_hours: int | None, justification: str) -> RoleGrantRequest:
    if not justification or not justification.strip():
        raise ValidationError('A justification is required.')
    return RoleGrantRequest.objects.create(
        requester=requester,
        group=group,
        duration_hours=duration_hours,
        justification=justification.strip(),
    )


def approve_request(grant_request: RoleGrantRequest, approver, decision_reason: str = '') -> RoleGrant:
    if grant_request.status != RoleGrantRequest.Status.PENDING:
        raise ValidationError('This request has already been decided.')
    if grant_request.requester_id == approver.id:
        raise PermissionDenied('You cannot approve your own request.')
    if not can_manage_role(approver, grant_request.group):
        raise PermissionDenied(
            "You can only approve requests for roles whose permissions are a "
            "subset of your own — you don't currently hold everything this role grants."
        )

    expires_at = None
    if grant_request.duration_hours:
        expires_at = timezone.now() + timedelta(hours=grant_request.duration_hours)

    grant = RoleGrant.objects.create(
        user=grant_request.requester,
        group=grant_request.group,
        granted_by=approver,
        expires_at=expires_at,
    )

    grant_request.status = RoleGrantRequest.Status.APPROVED
    grant_request.reviewed_by = approver
    grant_request.reviewed_at = timezone.now()
    grant_request.decision_reason = decision_reason
    grant_request.resulting_grant = grant
    grant_request.save(update_fields=[
        'status', 'reviewed_by', 'reviewed_at', 'decision_reason', 'resulting_grant',
    ])
    return grant


def deny_request(grant_request: RoleGrantRequest, approver, decision_reason: str = '') -> RoleGrantRequest:
    if grant_request.status != RoleGrantRequest.Status.PENDING:
        raise ValidationError('This request has already been decided.')
    if grant_request.requester_id == approver.id:
        raise PermissionDenied('You cannot deny your own request.')

    grant_request.status = RoleGrantRequest.Status.DENIED
    grant_request.reviewed_by = approver
    grant_request.reviewed_at = timezone.now()
    grant_request.decision_reason = decision_reason
    grant_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'decision_reason'])
    return grant_request


def cancel_request(grant_request: RoleGrantRequest, by_user) -> RoleGrantRequest:
    if grant_request.requester_id != by_user.id:
        raise PermissionDenied('You can only cancel your own requests.')
    if grant_request.status != RoleGrantRequest.Status.PENDING:
        raise ValidationError('This request has already been decided.')

    grant_request.status = RoleGrantRequest.Status.CANCELLED
    grant_request.save(update_fields=['status'])
    return grant_request


def revoke_grant(grant: RoleGrant, by_user) -> RoleGrant:
    if not can_manage_role(by_user, grant.group):
        raise PermissionDenied(
            "You can only revoke grants for roles whose permissions are a "
            "subset of your own."
        )
    grant.revoke(by_user)
    return grant


def pending_requests_for_approver(approver) -> list[RoleGrantRequest]:
    """
    Every pending request whose role the approver currently qualifies to
    approve (the subset rule) — this is the "anyone qualified" routing
    decision from the design brainstorm, not manager-specific routing.
    """
    if approver.is_superuser:
        return list(
            RoleGrantRequest.objects
            .filter(status=RoleGrantRequest.Status.PENDING)
            .exclude(requester=approver)
            .select_related('requester', 'group')
        )
    pending = (
        RoleGrantRequest.objects
        .filter(status=RoleGrantRequest.Status.PENDING)
        .exclude(requester=approver)
        .select_related('requester', 'group')
    )
    return [r for r in pending if can_manage_role(approver, r.group)]


def set_role_permissions(group: Group, codenames: list[str], acting_user) -> Group:
    """
    Define/replace a role's permission set. Restricted to whoever holds
    rbac.manage_roles at the call site (views.py) — this function assumes
    that check already passed and just does the work, but still enforces
    one more thing: you cannot grant a role permissions beyond your own,
    even with manage_roles, unless you're a superuser. Otherwise a
    non-superuser holder of manage_roles could mint a role more powerful
    than themselves and then grant it to someone else — a privilege-
    escalation path the subset rule exists specifically to close.
    """
    if not acting_user.is_superuser:
        own = get_effective_permissions(acting_user)
        overreach = set(codenames) - own
        if overreach:
            raise PermissionDenied(
                f"Cannot assign permissions you don't hold yourself: {', '.join(sorted(overreach))}"
            )

    permissions = []
    missing = []
    for full_codename in codenames:
        try:
            app_label, codename = full_codename.split('.', 1)
        except ValueError:
            missing.append(full_codename)
            continue
        try:
            permissions.append(
                Permission.objects.get(content_type__app_label=app_label, codename=codename)
            )
        except Permission.DoesNotExist:
            missing.append(full_codename)

    if missing:
        raise ValidationError(f'Unknown permission(s): {", ".join(missing)}')

    group.permissions.set(permissions)
    return group
