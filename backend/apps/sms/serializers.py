from rest_framework import serializers

from .models import SmsMessage


class SmsMessageSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    sender_name = serializers.SerializerMethodField()
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SmsMessage
        fields = [
            'id', 'customer', 'customer_name',
            'sender', 'sender_name',
            'phone', 'subject', 'body', 'status', 'status_label',
            'created_at',
        ]
        read_only_fields = ['id', 'sender', 'status', 'created_at']

    def get_customer_name(self, obj):
        c = obj.customer
        if not c:
            return ''
        return c.company_name or c.full_name or (c.user.username if c.user_id else '')

    def get_sender_name(self, obj):
        u = obj.sender
        if not u:
            return ''
        return u.get_full_name() or u.username
