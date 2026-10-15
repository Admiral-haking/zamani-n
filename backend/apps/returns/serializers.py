from rest_framework import serializers
from .models import ReturnRequest


class ReturnRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True
    )
    order_number = serializers.CharField(
        source='order.id',
        read_only=True
    )
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id', 
            'customer', 
            'customer_name',
            'order', 
            'order_number',
            'order_item', 
            'product_name', 
            'quantity',
            'reason', 
            'description',
            'status', 
            'image',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['customer', 'status', 'created_at', 'updated_at']