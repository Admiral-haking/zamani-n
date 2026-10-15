from django.db import transaction

from django.db.models import Sum
from rest_framework import serializers

from apps.accounts.models import User
from .models import Customer


class DistributorCustomerSerializer(serializers.ModelSerializer):
    """
    ایجاد مشتری توسط پخش‌کننده: ساخت اتمیک User + Customer
    به طوری که مشتری جدید زیرمجموعه همین پخش‌کننده و لاگین‌پذیر باشد.
    """

    username = serializers.CharField(write_only=True, max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    account_balance = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        read_only=True,
    )
    order_count = serializers.SerializerMethodField()
    total_purchased = serializers.SerializerMethodField()

    class Meta:

        model = Customer

        fields = (
            "id",
            "customer_code",
            "username",
            "password",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "company_name",
            "shop_name",
            "phone",
            "national_id",
            "address",
            "city",
            "postal_code",
            "tag",
            "is_active",
            "account_balance",
            "order_count",
            "total_purchased",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "customer_code",
            "is_active",
            "account_balance",
            "created_at",
            "updated_at",
        )

    def get_order_count(self, obj):
        annotated = getattr(obj, "orders_count", None)

        if annotated is None:
            return obj.orders.count()

        return annotated

    def get_total_purchased(self, obj):
        annotated = getattr(obj, "purchased_total", None)

        if annotated is None:
            annotated = obj.orders.aggregate(
                total=Sum("total_price")
            )["total"] or 0

        return int(annotated)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً گرفته شده است.")
        return value

    def validate_phone(self, value):
        if Customer.objects.filter(phone=value).exists() or \
                User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("این شماره قبلاً ثبت شده است.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        distributor = validated_data.pop("distributor")
        username = validated_data.pop("username")
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")

        user = User.objects.create(
            username=username,
            role=User.Role.CUSTOMER,
            phone=validated_data.get("phone") or "",
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save()

        # سیگنال post_save پروفایل مشتری را ساخته است؛ تکمیل می‌شود
        customer = getattr(user, "customer_profile", None)
        if customer is None:
            customer = Customer(user=user)
        for field, value in validated_data.items():
            setattr(customer, field, value)
        customer.distributor = distributor
        customer.save()
        return customer

    def update(self, instance, validated_data):
        # تغییر مشخصات پروفایل؛ رمز/نام کاربری از این مسیر قابل تغییر نیست
        validated_data.pop("username", None)
        validated_data.pop("password", None)
        validated_data.pop("first_name", None)
        validated_data.pop("last_name", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
