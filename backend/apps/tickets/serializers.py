from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.username',
        read_only=True
    )
    user_role = serializers.CharField(
        source='user.role',
        read_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'user_name', 'user_role',
            'title', 'message', 'category', 'priority',
            'status', 'admin_reply', 'admin_replied_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'user_name', 'user_role',
            'status', 'admin_reply', 'admin_replied_at',
            'created_at', 'updated_at'
        ]