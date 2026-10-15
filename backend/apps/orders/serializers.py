from rest_framework import serializers

import os

from .models import Order, OrderItem
from apps.payments.models import Payment



class OrderItemSerializer(serializers.ModelSerializer):


    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    discount = serializers.SerializerMethodField()


    class Meta:

        model = OrderItem

        fields = [

            "id",
            "product",
            "product_name",
            "quantity",
            "price",
            "discount"

        ]


    def get_discount(self, obj):
        product = obj.product
        if not product or not product.discount_percent or product.discount_percent <= 0:
            return 0
        per_unit = int(product.base_price) - int(obj.price)
        if per_unit <= 0:
            return 0
        return per_unit * obj.quantity




class OrderSerializer(serializers.ModelSerializer):


    items = OrderItemSerializer(
        many=True,
        read_only=True
    )


    customer_name = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    awaiting_approval = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()


    class Meta:

        model = Order


        fields = [

            "id",
            "customer",
            "customer_name",
            "status",
            "total_price",
            "total_discount",
            "paid_amount",
            "balance",
            "remaining_amount",
            "awaiting_approval",
            "debt_recorded",
            "payment_method",
            "payments",
            "tracking_code",
            "is_printed",
            "items",
            "created_at",
            "updated_at"

        ]


        read_only_fields = [

            "total_price",
            "paid_amount",
            "balance",
            "remaining_amount",
            "awaiting_approval",
            "debt_recorded",
            "payment_method",
            "created_at",
            "updated_at"

        ]


    def get_customer_name(self, obj):
        customer = obj.customer
        if not customer:
            return ""
        return (
            customer.company_name
            or customer.full_name
            or (customer.user.username if customer.user_id else "")
            or f"مشتری #{customer.id}"
        )


    def _success_payments(self, obj):
        return [p for p in obj.payments.all() if p.status == Payment.Status.SUCCESS]


    def get_paid_amount(self, obj):
        return sum(int(p.amount) for p in self._success_payments(obj))


    def get_balance(self, obj):
        return max(int(obj.total_price) - self.get_paid_amount(obj), 0)


    def get_remaining_amount(self, obj):
        # تا پیش از تأیید پخش‌کننده، فاکتور «مانده‌حساب» بدهی نیست؛
        # فاکتور لغو/برگشت‌خورده هم بدهی‌ای در حساب مشتری ندارد
        if (
            not obj.debt_recorded
            or obj.finance_reversed
            or obj.status == "CANCELLED"
        ):
            return 0

        return self.get_balance(obj)


    def get_awaiting_approval(self, obj):
        """درخواست خرید با مانده‌حساب که هنوز پخش‌کننده بررسی نکرده است."""
        return obj.status == "AWAITING_APPROVAL"


    def get_payment_method(self, obj):
        success = self._success_payments(obj)
        if success:
            return max(success, key=lambda p: (p.created_at, p.id)).method
        payments = list(obj.payments.all())
        if payments:
            return max(payments, key=lambda p: (p.created_at, p.id)).method
        return None


    def get_total_discount(self, obj):
        discount = 0
        items = obj.items.filter(
            product__discount_percent__gt=0
        ).values_list("price", "quantity", "product__base_price")
        for price, quantity, base_price in items:
            discount += (int(base_price) - int(price)) * quantity
        return max(discount, 0)


    def _receipt_url(self, payment):
        if not payment.receipt:
            return ""
        url = payment.receipt.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


    def get_payments(self, obj):
        request = self.context.get("request")
        result = []
        for p in obj.payments.all().order_by("-created_at"):
            result.append({
                "id": p.id,
                "amount": int(p.amount),
                "method": p.method,
                "status": p.status,
                "receipt": self._receipt_url(p),
                "receipt_name": os.path.basename(p.receipt.name) if p.receipt else "",
            })
        return result