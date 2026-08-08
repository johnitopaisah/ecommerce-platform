"""
RBAC API — role definitions, grants, and the request/approval workflow.

Role *definition* (creating/editing what a role grants) requires
rbac.manage_roles, checked at the view level via RequiresPermission.
Role *grant* (approving a request, revoking a grant) is delegatable and
checked dynamically per-request in services.py — the subset rule depends
on which specific role is involved, which a static view-level permission
class can't express, so those views only require IsAuthenticated and let
the service layer raise PermissionDenied when the subset check fails.
"""

from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.audit import log_admin_action
from . import services
from .models import RoleGrant, RoleGrantRequest
from .permissions import RequiresPermission, get_effective_permissions
from .serializers import (
    DecisionSerializer,
    GroupSerializer,
    GroupWriteSerializer,
    PermissionSerializer,
    RoleGrantRequestCreateSerializer,
    RoleGrantRequestSerializer,
    RoleGrantSerializer,
)


# ── Roles (Group definitions) ───────────────────────────────────────────────

@extend_schema(tags=['rbac'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def role_list(request):
    """GET is open to any authenticated user (needed for the request-a-role
    form). POST (defining a new role) requires rbac.manage_roles."""
    if request.method == 'GET':
        groups = Group.objects.prefetch_related('permissions__content_type').order_by('name')
        return Response(GroupSerializer(groups, many=True).data)

    if not RequiresPermission('rbac.manage_roles')().has_permission(request, None):
        raise PermissionDenied('You need rbac.manage_roles to define new roles.')

    serializer = GroupWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    group = Group.objects.create(name=serializer.validated_data['name'])
    services.set_role_permissions(
        group, serializer.validated_data.get('permission_codenames', []), request.user,
    )
    log_admin_action(request, 'role_create', f'Role: {group.name}')
    return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['rbac'])
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def role_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.method == 'GET':
        return Response(GroupSerializer(group).data)

    if not RequiresPermission('rbac.manage_roles')().has_permission(request, None):
        raise PermissionDenied('You need rbac.manage_roles to edit roles.')

    if request.method == 'DELETE':
        log_admin_action(request, 'role_delete', f'Role: {group.name}')
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = GroupWriteSerializer(group, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    if 'name' in serializer.validated_data:
        group.name = serializer.validated_data['name']
        group.save(update_fields=['name'])
    if 'permission_codenames' in serializer.validated_data:
        services.set_role_permissions(group, serializer.validated_data['permission_codenames'], request.user)
    log_admin_action(request, 'role_update', f'Role: {group.name}', dict(request.data))
    return Response(GroupSerializer(group).data)


@extend_schema(tags=['rbac'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permission_list(request):
    """Every available Permission — for building the role-edit picker UI."""
    permissions = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'codename',
    )
    return Response(PermissionSerializer(permissions, many=True).data)


# ── My access ────────────────────────────────────────────────────────────────

@extend_schema(tags=['rbac'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_permissions(request):
    """What the current user can actually do right now — union of active grants."""
    return Response({
        'is_superuser': request.user.is_superuser,
        'permissions': sorted(get_effective_permissions(request.user)),
    })


@extend_schema(tags=['rbac'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_grants(request):
    grants = (
        RoleGrant.objects
        .filter(user=request.user)
        .select_related('group', 'granted_by', 'revoked_by')
        .order_by('-granted_at')
    )
    return Response(RoleGrantSerializer(grants, many=True).data)


# ── Requests ─────────────────────────────────────────────────────────────────

@extend_schema(tags=['rbac'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def request_list_create(request):
    """GET — my own requests. POST — request a role."""
    if request.method == 'GET':
        requests_qs = (
            RoleGrantRequest.objects
            .filter(requester=request.user)
            .select_related('group', 'reviewed_by')
            .order_by('-created')
        )
        return Response(RoleGrantRequestSerializer(requests_qs, many=True).data)

    serializer = RoleGrantRequestCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    grant_request = services.request_role(
        requester=request.user,
        group=serializer.validated_data['group'],
        duration_hours=serializer.validated_data.get('duration_hours'),
        justification=serializer.validated_data['justification'],
    )
    return Response(
        RoleGrantRequestSerializer(grant_request).data, status=status.HTTP_201_CREATED,
    )


@extend_schema(tags=['rbac'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_requests(request):
    """Every pending request this user is currently qualified to approve."""
    pending = services.pending_requests_for_approver(request.user)
    return Response(RoleGrantRequestSerializer(pending, many=True).data)


@extend_schema(tags=['rbac'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_request(request, request_id):
    grant_request = get_object_or_404(RoleGrantRequest, id=request_id)
    serializer = DecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    grant = services.approve_request(grant_request, request.user, serializer.validated_data['reason'])

    log_admin_action(
        request, 'role_request_approve',
        f'{grant_request.requester} → {grant_request.group.name}',
        {'request_id': grant_request.id, 'grant_id': grant.id},
    )
    return Response(RoleGrantRequestSerializer(grant_request).data)


@extend_schema(tags=['rbac'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deny_request(request, request_id):
    grant_request = get_object_or_404(RoleGrantRequest, id=request_id)
    serializer = DecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    services.deny_request(grant_request, request.user, serializer.validated_data['reason'])

    log_admin_action(
        request, 'role_request_deny',
        f'{grant_request.requester} → {grant_request.group.name}',
        {'request_id': grant_request.id},
    )
    return Response(RoleGrantRequestSerializer(grant_request).data)


@extend_schema(tags=['rbac'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_request(request, request_id):
    grant_request = get_object_or_404(RoleGrantRequest, id=request_id)
    services.cancel_request(grant_request, request.user)
    return Response(RoleGrantRequestSerializer(grant_request).data)


# ── Grants ───────────────────────────────────────────────────────────────────

@extend_schema(tags=['rbac'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grant_list(request):
    """Admin visibility across all grants, optionally filtered by user.
    Requires rbac.grant_roles or manage_users — plain staff shouldn't be
    able to enumerate everyone else's access."""
    if not (
        RequiresPermission('rbac.grant_roles')().has_permission(request, None)
        or RequiresPermission('account.manage_users')().has_permission(request, None)
    ):
        raise PermissionDenied('You need rbac.grant_roles or account.manage_users to view this.')

    grants = RoleGrant.objects.select_related('user', 'group', 'granted_by', 'revoked_by').order_by('-granted_at')
    user_id = request.query_params.get('user')
    if user_id:
        grants = grants.filter(user_id=user_id)
    return Response(RoleGrantSerializer(grants, many=True).data)


@extend_schema(tags=['rbac'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_grant(request, grant_id):
    grant = get_object_or_404(RoleGrant, id=grant_id)
    services.revoke_grant(grant, request.user)
    log_admin_action(request, 'role_grant_revoke', f'{grant.user} — {grant.group.name}', {'grant_id': grant.id})
    return Response(RoleGrantSerializer(grant).data)
