from rest_framework import serializers

from .models import Order, OrderItem



class OrderItemSerializer(serializers.ModelSerializer):


    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )


    class Meta:

        model = OrderItem

        fields = [

            "id",
            "product",
            "product_name",
            "quantity",
            "price"

        ]




class OrderSerializer(serializers.ModelSerializer):


    items = OrderItemSerializer(
        many=True,
        read_only=True
    )


    customer_name = serializers.CharField(
        source="customer.company_name",
        read_only=True
    )


    class Meta:

        model = Order


        fields = [

            "id",
            "customer",
            "customer_name",
            "status",
            "total_price",
            "tracking_code",
            "items",
            "created_at",
            "updated_at"

        ]


        read_only_fields = [

            "total_price",
            "created_at",
            "updated_at"

        ]