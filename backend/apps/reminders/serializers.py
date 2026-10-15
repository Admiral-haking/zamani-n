from rest_framework import serializers

from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = [
            'id', 'customer', 'customer_name', 'customer_phone',
            'created_by', 'created_by_name',
            'title', 'message', 'remind_at', 'is_done',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_customer_name(self, obj):
        c = obj.customer
        if not c:
            return ''
        return c.company_name or c.full_name or (c.user.username if c.user_id else f'مشتری #{c.id}')

    def get_created_by_name(self, obj):
        u = obj.created_by
        if not u:
            return ''
        return u.get_full_name() or u.username
