from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.distributors.models import Distributor

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    password2 = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            "username",
            "phone",
            "password",
            "password2",
        )

    def validate(self, attrs):

        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {
                    "password": "Passwords do not match."
                }
            )

        return attrs

    def create(self, validated_data):

        validated_data.pop("password2")

        password = validated_data.pop("password")

        user = User(
            username=validated_data["username"],
            phone=validated_data["phone"],
            role=User.Role.CUSTOMER
        )

        user.set_password(password)

        user.save()

        return user


class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):

        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(
            username=username,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                "Username or password is incorrect."
            )

        attrs["user"] = user

        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = (
            "id",
            "username",
            "phone",
            "role",
            "email",
            "first_name",
            "last_name",
        )


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    ویرایش پروفایل کاربر جاری (نام، نام کاربری، ایمیل، شماره تماس).
    """

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone",
        )

    def validate_username(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("نام کاربری نمی‌تواند خالی باشد.")
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("نام کاربری باید حداقل ۳ کاراکتر باشد.")
        qs = User.objects.filter(username=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("این نام کاربری قبلاً گرفته شده است.")
        return value

    def validate_phone(self, value):
        if value:
            qs = User.objects.filter(phone=value)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("این شماره قبلاً ثبت شده است.")
        return value

    def validate_email(self, value):
        if value:
            qs = User.objects.filter(email=value)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    تغییر رمز عبور کاربر جاری با تأیید رمز قبلی.
    """

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=6,
    )

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError(
                {"old_password": "رمز عبور فعلی صحیح نیست."}
            )
        return attrs


class AccountCreateSerializer(serializers.ModelSerializer):
    """
    ساخت حساب کاربری توسط ادمین کل / منشی.

    ثبت‌نام آزاد وجود ندارد؛ تنها این endpoint ها حساب می‌سازند:
      - پخش‌کننده  (ادمین/منشی)
      - منشی       (فقط ادمین کل)
      - مشتری      (ادمین/منشی؛ بدون distributor_id زیرمجموعه ادمین کل است)
    """

    distributor_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="فقط برای مشتری: شناسه پخش‌کننده معرف",
    )

    company_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="فقط برای مشتری: نام کسب‌وکار",
    )

    national_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    postal_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    tag = serializers.CharField(write_only=True, required=False, allow_blank=True)

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:

        model = User

        fields = (
            "username",
            "password",
            "phone",
            "first_name",
            "last_name",
            "distributor_id",
            "company_name",
            "national_code",
            "address",
            "postal_code",
            "tag",
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً گرفته شده است.")
        return value

    def validate_phone(self, value):
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("این شماره قبلاً ثبت شده است.")
        return value

    def validate_distributor_id(self, value):
        if value is not None and not Distributor.objects.filter(pk=value).exists():
            raise serializers.ValidationError("پخش‌کننده یافت نشد.")
        return value
