from rest_framework import serializers

from apps.products.models import Product, ProductDiscount


class ProductDiscountSerializer(serializers.ModelSerializer):
    """سریالایزر تخفیف محصول (ثبت‌شده توسط منشی)"""

    class Meta:
        model = ProductDiscount
        fields = [
            "id",
            "product_name",
            "percent",
            "code",
            "start_date",
            "end_date",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]

    def validate_percent(self, value):
        if value < 1 or value > 100:
            raise serializers.ValidationError(
                "درصد تخفیف باید بین ۱ تا ۱۰۰ باشد."
            )
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["created_by"] = request.user
        instance = super().create(validated_data)
        self._sync_product_discount(instance)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._sync_product_discount(instance)
        return instance

    def _sync_product_discount(self, instance):
        """اعمال همان درصد تخفیف روی محصول اصلی (برای سایت مادر)"""
        Product.objects.filter(name__iexact=instance.product_name).update(
            discount_percent=instance.percent
        )