from rest_framework import serializers

from apps.distributors.models import Distributor
from .models import ProductPrice, DistributorPrice


class ProductPriceSerializer(serializers.ModelSerializer):
    """(منسوخ) قیمت‌گذاری قدیمی per-customer — از جریان خرید حذف شده است."""

    class Meta:

        model = ProductPrice

        fields = "__all__"


class CustomerPriceSerializer(serializers.ModelSerializer):
    """
    قیمت دستی هر مشتری برای هر محصول (ست‌شده توسط پخش‌کننده خودش).

    مشتری فقط قیمت‌های خودش را می‌بیند؛ پخش‌کننده فقط مشتریان خودش را.
    """

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    base_price = serializers.DecimalField(
        source="product.base_price",
        max_digits=12,
        decimal_places=0,
        read_only=True,
    )

    customer_name = serializers.SerializerMethodField()

    class Meta:

        model = ProductPrice

        fields = (
            "id",
            "customer",
            "customer_name",
            "product",
            "product_name",
            "base_price",
            "price",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def get_customer_name(self, obj):
        c = obj.customer
        if not c:
            return ""
        return c.company_name or c.full_name or (
            c.user.username if c.user_id else f"مشتری #{c.id}"
        )

    def validate_price(self, value):

        if value <= 0:

            raise serializers.ValidationError("قیمت باید بزرگ‌تر از صفر باشد.")

        return value


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
