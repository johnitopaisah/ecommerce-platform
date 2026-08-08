from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from .models import RoleGrant, RoleGrantRequest


class PermissionSerializer(serializers.ModelSerializer):
    codename_full = serializers.SerializerMethodField()
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)

    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename', 'codename_full', 'app_label')

    def get_codename_full(self, obj):
        return f'{obj.content_type.app_label}.{obj.codename}'


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_count = serializers.IntegerField(source='permissions.count', read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions', 'permission_count')


class GroupWriteSerializer(serializers.ModelSerializer):
    """Role definition — name + a flat list of 'app_label.codename' strings."""
    permission_codenames = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False, default=list,
    )

    class Meta:
        model = Group
        fields = ('id', 'name', 'permission_codenames')


class RoleGrantSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    granted_by_email = serializers.CharField(source='granted_by.email', read_only=True, default=None)
    revoked_by_email = serializers.CharField(source='revoked_by.email', read_only=True, default=None)
    is_currently_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = RoleGrant
        fields = (
            'id', 'user', 'user_email', 'group', 'group_name',
            'granted_by', 'granted_by_email', 'granted_at', 'expires_at',
            'status', 'is_currently_valid',
            'revoked_by', 'revoked_by_email', 'revoked_at', 'reason',
        )
        read_only_fields = fields


class RoleGrantRequestSerializer(serializers.ModelSerializer):
    requester_email = serializers.CharField(source='requester.email', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    reviewed_by_email = serializers.CharField(source='reviewed_by.email', read_only=True, default=None)

    class Meta:
        model = RoleGrantRequest
        fields = (
            'id', 'requester', 'requester_email', 'group', 'group_name',
            'duration_hours', 'justification', 'status',
            'reviewed_by', 'reviewed_by_email', 'reviewed_at', 'decision_reason',
            'resulting_grant', 'created',
        )
        read_only_fields = (
            'id', 'requester', 'requester_email', 'group_name', 'status',
            'reviewed_by', 'reviewed_by_email', 'reviewed_at', 'decision_reason',
            'resulting_grant', 'created',
        )


class RoleGrantRequestCreateSerializer(serializers.Serializer):
    group_id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), source='group')
    duration_hours = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    justification = serializers.CharField(max_length=2000)


class DecisionSerializer(serializers.Serializer):
    """Body for approve/deny actions."""
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
