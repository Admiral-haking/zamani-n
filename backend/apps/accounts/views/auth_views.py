from django.db import transaction

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.distributors.models import Distributor

from apps.accounts.serializers import (
    LoginSerializer,
    UserSerializer,
    AccountCreateSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer,
)

from apps.audit.services import AuditService


class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and (request.user.is_superuser or request.user.role in ["ADMIN", "SECRETARY"])
        )


class IsAdminOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and (request.user.is_superuser or request.user.role == "ADMIN")
        )


class BaseAccountCreateView(APIView):

    role = None  # نقشی که این ویو می‌سازد
    admin_only = False

    def get_permissions(self):
        if self.admin_only:
            return [permissions.IsAuthenticated(), IsAdminOnlyPermission()]
        return [permissions.IsAuthenticated(), IsStaffPermission()]

    @transaction.atomic
    def post(self, request):
        serializer = AccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        distributor_id = data.pop("distributor_id", None)
        company_name = data.pop("company_name", "")
        national_code = data.pop("national_code", "")
        address = data.pop("address", "")
        postal_code = data.pop("postal_code", "")
        tag = data.pop("tag", "")
        password = data.pop("password")

        if self.role == User.Role.CUSTOMER and distributor_id is None \
                and not (request.user.is_superuser or request.user.role == "ADMIN"):
            raise permissions.PermissionDenied(
                "منشی فقط می‌تواند مشتریِ یک پخش‌کننده را بسازد."
            )

        user = User.objects.create_user(
            username=data["username"],
            phone=data.get("phone") or None,
            first_name=data.get("first_name") or "",
            last_name=data.get("last_name") or "",
            role=self.role,
            national_code=national_code or None,
        )
        user.set_password(password)
        user.save()

        profile_note = ""
        if self.role == User.Role.DISTRIBUTOR:
            # سیگنال post_save پروفایل می‌سازد؛ اطلاعات تکمیلی به‌روز می‌شود
            Distributor.objects.filter(user=user).update(
                full_name=f"{data.get('first_name') or ''} {data.get('last_name') or ''}".strip()
                or user.username
            )
            profile_note = "distributor_profile"
        elif self.role == User.Role.CUSTOMER:
            customer = getattr(user, "customer_profile", None)
            if customer is None:
                customer = Customer.objects.create(user=user, phone=data.get("phone") or "")
            if data.get("phone"):
                customer.phone = data["phone"]
            if company_name:
                customer.company_name = company_name
            if national_code:
                customer.national_id = national_code
            if address:
                customer.address = address
            if postal_code:
                customer.postal_code = postal_code
            if tag:
                customer.tag = tag
            if self.role == User.Role.CUSTOMER and distributor_id is not None:
                customer.distributor_id = distributor_id
            customer.save()
            profile_note = "customer_profile"

        AuditService.log(
            user=request.user,
            action="CREATE",
            model_name="User",
            object_id=user.id,
            description=(
                f"{self.role} account '{user.username}' created "
                f"by {request.user.username}"
            ),
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "profile": profile_note,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Accounts"])
class CreateDistributorView(BaseAccountCreateView):
    role = User.Role.DISTRIBUTOR


@extend_schema(tags=["Accounts"])
class CreateSecretaryView(BaseAccountCreateView):
    role = User.Role.SECRETARY
    admin_only = True


@extend_schema(tags=["Accounts"])
class CreateCustomerByStaffView(BaseAccountCreateView):
    role = User.Role.CUSTOMER


@extend_schema(
    tags=["Accounts"],
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful. Returns JWT tokens and user information."
        )
    },
)
class LoginView(APIView):

    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({

            "refresh": str(refresh),

            "access": str(refresh.access_token),

            "user": UserSerializer(user).data

        })


@extend_schema(
    tags=["Accounts"],
    responses=UserSerializer,
)
class MeView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial=False):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        fields = ["first_name", "last_name", "username", "email", "phone"]
        for field in fields:
            if field in serializer.validated_data:
                setattr(request.user, field, serializer.validated_data[field])
        request.user.save(update_fields=fields)
        return Response(UserSerializer(request.user).data)


@extend_schema(
    tags=["Accounts"],
    request=ChangePasswordSerializer,
    responses={200: OpenApiResponse(description="Password changed successfully.")},
)
class ChangePasswordView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        AuditService.log(
            user=request.user,
            action="UPDATE",
            model_name="User",
            object_id=request.user.id,
            description=f"Password changed for {request.user.username}",
        )
        return Response(
            {"success": True, "message": "رمز عبور با موفقیت تغییر کرد."},
            status=status.HTTP_200_OK,
        )
