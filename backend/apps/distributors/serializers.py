from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Distributor, DistributorPurchase

from apps.customers.models import Customer


User = get_user_model()


class DistributorSerializer(serializers.ModelSerializer):


    username = serializers.CharField(
        write_only=True
    )


    password = serializers.CharField(
        write_only=True
    )


    role = serializers.CharField(
        source="user.role",
        read_only=True
    )


    class Meta:

        model = Distributor

        fields = (
            "id",
            "username",
            "password",
            "distributor_code",
            "full_name",
            "phone",
            "city",
            "address",
            "commission_percent",
            "is_active",
            "role",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "distributor_code",
            "commission_percent",
            "is_active",
            "role",
            "created_at",
            "updated_at",
        )


    def validate_username(
        self,
        value
    ):

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")

        return value


    def validate_phone(
        self,
        value
    ):

        if not value:
            return value

        qs = Distributor.objects.filter(phone=value)

        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists() or \
                Customer.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone already exists.")

        return value


    def create(
        self,
        validated_data
    ):

        username = validated_data.pop("username")

        password = validated_data.pop("password")

        user = User.objects.create(
            username=username,
            role=User.Role.DISTRIBUTOR,
            phone=validated_data.get("phone")
        )

        user.set_password(password)

        user.save()

        # سیگنال post_save پروفایل پخش‌کننده را ساخته است؛ فقط تکمیل می‌شود
        distributor = Distributor.objects.get(user=user)

        for field, value in validated_data.items():
            if field != "phone":
                setattr(distributor, field, value)

        distributor.save()

        return distributor


class DistributorPurchaseSerializer(serializers.ModelSerializer):
    distributor_name = serializers.SerializerMethodField()

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    created_at_label = serializers.SerializerMethodField()

    class Meta:

        model = DistributorPurchase

        fields = (
            "id",
            "distributor",
            "distributor_name",
            "items",
            "total_amount",
            "status",
            "status_label",
            "created_at",
            "created_at_label",
            "updated_at",
        )

        read_only_fields = (
            "distributor",
            "total_amount",
            "status",
            "created_at",
            "updated_at",
        )

    def get_distributor_name(self, obj):
        if obj.distributor:
            return obj.distributor.full_name
        return obj.distributor_name or ""

    def get_created_at_label(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M") if obj.created_at else ""

    def validate_items(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("اقلام باید لیست باشند.")

        products = []
        for raw in value:
            if not isinstance(raw, dict):
                raise serializers.ValidationError("قالب اقلام نامعتبر است.")
            product_id = raw.get("product_id") or raw.get("product")
            if not product_id:
                raise serializers.ValidationError("شناسه محصول الزامی است.")
            try:
                quantity = int(raw.get("quantity") or 0)
            except (TypeError, ValueError):
                quantity = 0
            if quantity <= 0:
                raise serializers.ValidationError("تعداد باید بزرگ‌تر از صفر باشد.")
            try:
                price = int(raw.get("price") or 0)
            except (TypeError, ValueError):
                price = 0
            if price < 0:
                raise serializers.ValidationError("قیمت نمی‌تواند منفی باشد.")
            products.append({
                "product_id": int(product_id),
                "product_name": raw.get("product_name") or "",
                "unit": raw.get("unit") or "package",
                "quantity": quantity,
                "price": price,
                "total": price * quantity,
            })

        if not products:
            raise serializers.ValidationError("حداقل یک قلم محصول الزامی است.")

        return products

    def create(self, validated_data):
        total = sum(
            int(item["price"]) * int(item["quantity"])
            for item in validated_data.get("items", [])
        )
        validated_data["total_amount"] = total
        distributor = validated_data.get("distributor")
        if distributor and not validated_data.get("distributor_name"):
            validated_data["distributor_name"] = distributor.full_name
        return super().create(validated_data)