import re

from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.distributors.models import Distributor

from .models import Customer, CustomerBackup



User = get_user_model()




class CustomerSerializer(serializers.ModelSerializer):


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

    full_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True,
    )

    email = serializers.CharField(
        source="user.email",
        read_only=True,
    )

    distributor = serializers.PrimaryKeyRelatedField(
        queryset=Distributor.objects.all(),
        required=False,
        allow_null=True,
    )

    distributor_name = serializers.CharField(
        source="distributor.full_name",
        read_only=True,
        default=None,
    )

    total_orders = serializers.IntegerField(
        read_only=True,
    )

    total_spent = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
    )


    last_purchase_at = serializers.SerializerMethodField()



    class Meta:


        model = Customer


        fields = (

            "id",

            "username",

            "password",

            "customer_code",

            "company_name",

            "shop_name",

            "phone",

            "national_id",

            "address",

            "postal_code",

            "city",

            "state",

            "account_balance",

            "price_list",

            "discount_list",

            "is_active",

            "role",

            "full_name",

            "email",

            "distributor_name",

            "distributor",

            "total_orders",

            "total_spent",

            "last_purchase_at",

            "created_at",

            "updated_at",

        )



        read_only_fields = (

            "created_at",

            "updated_at",

            "account_balance",

            "role",

            "full_name",

            "email",

            "distributor_name",

            "total_orders",

            "total_spent",

        )



    def get_last_purchase_at(self, obj):
        return getattr(obj, 'last_purchase_at', None)





    def validate_username(

        self,

        value

    ):


        if User.objects.filter(

            username=value

        ).exclude(pk=getattr(self.instance, "user_id", None)).exists():


            raise serializers.ValidationError(

                "Username already exists."

            )


        return value




    def validate_phone(

        self,

        value

    ):


        if re.fullmatch(r"[0-9]{10,11}", str(value)) is None:

            raise serializers.ValidationError(

                "Phone must contain 10-11 digits."

            )


        if User.objects.filter(

            phone=value

        ).exclude(pk=getattr(self.instance, "user_id", None)).exists():


            raise serializers.ValidationError(

                "Phone already exists."

            )


        return value




    def create(

        self,

        validated_data

    ):


        username = validated_data.pop(

            "username"

        )


        password = validated_data.pop(

            "password"

        )



        user = User.objects.create(

            username=username,

            role=User.Role.CUSTOMER,

            phone=validated_data.get("phone")

        )



        user.set_password(

            password

        )


        user.save()



        # سیگنال post_save پروفایل مشتری را ساخته است؛ فقط تکمیل می‌شود

        customer = Customer.objects.get(user=user)


        for field, value in validated_data.items():

            if field != "phone":

                setattr(customer, field, value)


        customer.save()


        from .services import sync_customer_backup
        sync_customer_backup(
            customer,
            actor=getattr(self.context.get("request"), "user", None)
        )

        return customer


    def update(self, instance, validated_data):

        password = validated_data.pop("password", None)
        username = validated_data.pop("username", None)

        if instance.user_id:
            user = instance.user
            updates = []
            if username:
                user.username = username
                updates.append("username")
            if password:
                user.set_password(password)
                updates.append("password")
            if updates:
                user.save(update_fields=updates)

        # تلفن متعلق به کاربر است، پس مستقیم روی user ذخیره می‌شود
        phone = validated_data.pop("phone", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        if phone:
            user = instance.user
            user.phone = phone
            user.save(update_fields=["phone"])

        from .services import sync_customer_backup
        sync_customer_backup(
            instance,
            actor=getattr(self.context.get("request"), "user", None)
        )

        return instance






class CustomerBackupSerializer(serializers.ModelSerializer):

    display_name = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = CustomerBackup
        fields = (
            "id",
            "original_customer_id",
            "customer_code",
            "username",
            "full_name",
            "company_name",
            "shop_name",
            "phone",
            "national_id",
            "distributor_name",
            
            "account_balance",
            "balance",
            "display_name",
            "is_deleted",
            "deleted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_display_name(self, obj):
        return obj.full_name or obj.company_name or obj.phone or ''

    def get_balance(self, obj):
        return int(obj.account_balance)


class DistributorCustomerSerializer(

    serializers.ModelSerializer

):


    class Meta:


        model = Customer


        fields = (

            "id",

            "customer_code",

            "company_name",

            "phone",

            "address",

            "account_balance",

            "is_active",

        )



        read_only_fields = (

            "account_balance",

        )