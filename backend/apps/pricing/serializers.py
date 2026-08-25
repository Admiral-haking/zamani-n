from rest_framework import serializers

from apps.distributors.models import Distributor
from .models import ProductPrice, DistributorPrice


class ProductPriceSerializer(serializers.ModelSerializer):
    """(منسوخ) قیمت‌گذاری قدیمی per-customer — از جریان خرید حذف شده است."""

    class Meta:

        model = ProductPrice

        fields = "__all__"


class DistributorPriceSerializer(serializers.ModelSerializer):
    """
    قیمت فروشگاهِ پخش‌کننده برای یک محصول.

    پخش‌کننده فقط قیمت‌های فروشگاه خودش را می‌بیند و ویرایش می‌کند؛
    ادمین کل/منشی با ارسال distributor_id قیمت هر پخش‌کننده‌ای را
    می‌توانند ثبت کنند.
    """

    distributor_name = serializers.CharField(
        source="distributor.full_name", read_only=True
    )
    product_name = serializers.CharField(
        source="product.name", read_only=True
    )
    base_price = serializers.DecimalField(
        source="product.base_price",
        max_digits=12,
        decimal_places=0,
        read_only=True,
    )

    class Meta:

        model = DistributorPrice

        fields = (
            "id",
            "distributor",
            "distributor_name",
            "product",
            "product_name",
            "base_price",
            "price",
            "created_at",
            "updated_at",
        )

        read_only_fields = ("distributor", "created_at", "updated_at")

    def validate_price(self, value):

        if value <= 0:

            raise serializers.ValidationError("قیمت باید بزرگ‌تر از صفر باشد.")

        return value

    def validate_product(self, product):

        if not product.is_active:

            raise serializers.ValidationError("محصول غیرفعال است.")

        return product
