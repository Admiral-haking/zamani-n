from rest_framework import serializers
import os
from .models import Ticket, TicketMessage, TicketAttachment
from apps.customers.models import Customer


class TicketAttachmentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = ['id', 'name', 'url', 'size', 'created_at']

    def get_name(self, obj):
        if obj.file:
            return os.path.basename(obj.file.name)
        return ''

    def get_url(self, obj):
        if obj.file:
            return obj.file.url
        return ''

    def get_size(self, obj):
        try:
            return obj.file.size or 0
        except Exception:
            return 0


class TicketMessageSerializer(serializers.ModelSerializer):
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        fields = ['id', 'sender', 'sender_name', 'text', 'attachments', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()
    user_company = serializers.SerializerMethodField()
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'user_name', 'user_role', 'user_phone', 'user_company',
            'guest_name', 'guest_phone', 'guest_email',
            'title', 'message', 'category', 'status',
            'admin_reply', 'admin_replied_at',
            'customer_reply', 'customer_replied_at',
            'messages',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'user_name', 'user_role', 'user_phone', 'user_company',
            'status', 'admin_reply', 'admin_replied_at',
            'customer_reply', 'customer_replied_at',
            'messages',
            'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return obj.guest_name or 'مهمان'

    def get_user_role(self, obj):
        if obj.user:
            return obj.user.role
        return 'GUEST'

    def get_user_phone(self, obj):
        if obj.user:
            return obj.user.phone or ''
        return obj.guest_phone or ''

    def get_user_company(self, obj):
        if obj.user_id:
            customer = Customer.objects.filter(user_id=obj.user_id).first()
            if customer:
                return customer.company_name or ''
        return ''
