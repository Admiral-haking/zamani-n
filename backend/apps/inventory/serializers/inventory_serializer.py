from rest_framework import serializers

from apps.inventory.models import Inventory, InventoryLog


class InventoryLogSerializer(serializers.ModelSerializer):

    recorded_by = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    class Meta:

        model = InventoryLog

        fields = [
            "id",
            "product",
            "category",
            "unit",
            "quantity",
            "direction",
            "recorded_by",
            "created_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["recorded_by"] = request.user
        return super().create(validated_data)


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
            "package_quantity",
            "carton_quantity",
            "minimum_stock",
            "is_low_stock",
            "updated_at",
        ]
