from rest_framework import serializers

from django.db.models import Q

from apps.products.models import Product
from apps.pricing.models import DistributorPrice


class ProductSerializer(serializers.ModelSerializer):

    effective_price = serializers.SerializerMethodField()
    price_source = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def _viewer_shop(self):
        """پخش‌کننده مرتبط با کاربرِ در حال مشاهده (مشتری → معرف، پخش‌کننده → خودش)"""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        if user.role == "CUSTOMER" and hasattr(user, "customer_profile"):
            return user.customer_profile.distributor
        if user.role == "DISTRIBUTOR" and hasattr(user, "distributor_profile"):
            return user.distributor_profile
        return None

    def get_effective_price(self, obj):
        """قیمت مؤثر: قیمت فروشگاهِ پخش‌کننده مرتبط، وگرنه قیمت پایه"""
        shop = self._viewer_shop()
        if shop is None:
            # ادمین/منشی قیمت پایه شرکت را می‌بینند
            return obj.base_price
        price = (
            DistributorPrice.objects
            .filter(distributor=shop, product=obj)
            .values_list("price", flat=True)
            .first()
        )
        return price if price is not None else obj.base_price

    def get_price_source(self, obj):
        shop = self._viewer_shop()
        if shop is None:
            return "BASE"
        priced = DistributorPrice.objects.filter(
            distributor=shop, product=obj
        ).exists()
        return "DISTRIBUTOR" if priced else "BASE"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # قیمت پایه فقط برای مدیران؛ بقیه قیمت مؤثر می‌بینند (نیاز کارفرما)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        is_staff_view = bool(
            user and getattr(user, "is_authenticated", False) and
            (user.is_superuser or user.role in ["ADMIN", "SECRETARY"])
        )
        if not is_staff_view:
            data["base_price"] = data["effective_price"]
            data.pop("effective_price", None)
            data.pop("price_source", None)
        return data
