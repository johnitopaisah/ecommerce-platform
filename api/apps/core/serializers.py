from rest_framework import serializers
from .models import AdminActionLog


class AdminActionLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source='actor.email', read_only=True, default=None)

    class Meta:
        model = AdminActionLog
        fields = (
            'id', 'actor', 'actor_email', 'action', 'target',
            'outcome', 'detail', 'ip_address', 'created',
        )
        read_only_fields = fields
