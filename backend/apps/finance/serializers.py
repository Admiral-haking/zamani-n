from rest_framework import serializers

import os

from .models import Transaction, Check
from apps.customers.models import Customer



class TransactionSerializer(serializers.ModelSerializer):

    paid_amount = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    payment_id = serializers.SerializerMethodField()
    payment_receipt = serializers.SerializerMethodField()
    payment_receipt_name = serializers.SerializerMethodField()
    order_invoice = serializers.SerializerMethodField()
    order_products = serializers.SerializerMethodField()

    class Meta:

        model = Transaction

        fields = "__all__"

        read_only_fields = (
            "created_at",
            "updated_at",
            "deleted_at",
            "is_deleted",
        )

    def get_paid_amount(self, obj):
        if obj.transaction_type in (Transaction.Type.PAYMENT, Transaction.Type.RETURN):
            return int(obj.amount)
        return 0

    def get_balance(self, obj):
        if obj.customer_id:
            return int(obj.customer.account_balance)
        return 0

    def get_payment_id(self, obj):
        return obj.payment_id

    def get_payment_receipt(self, obj):
        if not (obj.payment_id and getattr(obj.payment, "receipt", None)):
            return ""
        url = obj.payment.receipt.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_payment_receipt_name(self, obj):
        if not (obj.payment_id and getattr(obj.payment, "receipt", None)):
            return ""
        return os.path.basename(obj.payment.receipt.name)

    def get_payment_method(self, obj):
        if obj.payment_id:
            return obj.payment.method
        return None

    def get_status(self, obj):
        if obj.transaction_type == Transaction.Type.ORDER_DEBT:
            return "PENDING"
        return "SUCCESS"

    def get_status_label(self, obj):
        if obj.transaction_type == Transaction.Type.ORDER_DEBT:
            return "در انتظار پرداخت"
        if obj.transaction_type == Transaction.Type.PAYMENT:
            return "پرداخت شده"
        if obj.transaction_type == Transaction.Type.RETURN:
            return "برگشتی"
        return "تصحیح حساب"

    def get_order_invoice(self, obj):
        order = getattr(obj, "order", None)
        if not order:
            return ""
        return order.tracking_code or f"#{order.id}"

    def get_order_products(self, obj):
        order = getattr(obj, "order", None)
        if not order:
            return []
        items = []
        try:
            qs = order.items.select_related("product").all()
        except Exception:
            return []
        for item in qs:
            name = ""
            try:
                name = item.product.name if item.product_id else ""
            except Exception:
                name = ""
            items.append({
                "name": name or "محصول",
                "quantity": item.quantity,
                "price": int(item.price or 0),
            })
        return items



class CheckSerializer(serializers.ModelSerializer):

    customer_name = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    customer_national_id = serializers.SerializerMethodField()
    customer_info = serializers.SerializerMethodField()
    registered_by = serializers.CharField(read_only=True)
    registered_by_label = serializers.SerializerMethodField()

    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:

        model = Check

        fields = "__all__"

        read_only_fields = (
            "created_at",
            "updated_at",
            "deleted_at",
            "is_deleted",
            "status",
            "registered_by",
        )

    def get_customer_name(self, obj):
        if obj.customer_id:
            return obj.customer.company_name or obj.customer.user.get_full_name() or (
                obj.customer.user.username if obj.customer.user_id else ""
            ) or ""
        return ""

    def get_company_name(self, obj):
        if obj.customer_id:
            return obj.customer.company_name or ""
        return ""

    def get_customer_phone(self, obj):
        if obj.customer_id:
            return obj.customer.phone or ""
        return ""

    def get_customer_national_id(self, obj):
        if obj.customer_id:
            return obj.customer.national_id or ""
        return ""

    def get_customer_info(self, obj):
        if not obj.customer_id:
            return None
        c = obj.customer
        return {
            "id": c.id,
            "company_name": c.company_name or "",
            "shop_name": c.shop_name or "",
            "full_name": c.user.get_full_name() if c.user_id else "",
            "phone": c.phone or "",
            "national_id": c.national_id or "",
        }

    def get_registered_by_label(self, obj):
        labels = {
            "CUSTOMER": "مشتری",
            "SECRETARY": "منشی",
            "ADMIN": "ادمین",
            "DISTRIBUTOR": "پخش‌کننده",
        }
        return labels.get(obj.registered_by, obj.registered_by or "منشی")

    def get_status_label(self, obj):
        labels = {
            Check.Status.PENDING: "در انتظار بررسی",
            Check.Status.APPROVED: "تایید شده",
            Check.Status.REJECTED: "رد شده",
            Check.Status.PAID: "پرداخت شده",
        }
        return labels.get(obj.status, obj.status)