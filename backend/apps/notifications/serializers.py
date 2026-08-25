from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_name',
            'title', 'message', 'type',
            'is_read', 'is_deleted',
            'created_at'
        ]
        read_only_fields = [
            'user', 'user_name',
            'created_at'
        ]