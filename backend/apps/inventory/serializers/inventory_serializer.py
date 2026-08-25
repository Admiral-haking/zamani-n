from rest_framework import serializers

from apps.inventory.models import Inventory


class InventorySerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )


    is_low_stock = serializers.BooleanField(
        read_only=True
    )


    class Meta:

        model = Inventory

        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "minimum_stock",
            "is_low_stock",
            "updated_at",
        ]