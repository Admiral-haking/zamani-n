from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DistributorPrice, ProductPrice

from .serializers import (
    DistributorPriceSerializer,
    ProductPriceSerializer,
)

from apps.distributors.models import Distributor


def _is_staff(user):
    return user.is_superuser or user.role in ["ADMIN", "SECRETARY"]


class DistributorPriceViewSet(viewsets.ModelViewSet):
    """
    فروشگاهِ پخش‌کننده: تعیین قیمت محصولات در پنل خودش.

    - DISTRIBUTOR: فقط قیمت‌های فروشگاه خودش (distributor خودکار ثبت می‌شود)
    - ADMIN/SECRETARY: با ارسال distributor_id قیمت هر پخش‌کننده‌ای را
      می‌توانند ثبت و مشاهده کنند
    - CUSTOMER: فقط خواندن قیمت‌های معرف خودش
    """

    serializer_class = DistributorPriceSerializer

    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ["product", "product__category"]

    search_fields = ["product__name", "product__code"]

    ordering_fields = ["price", "updated_at"]

    ordering = ["product__name"]

    def get_permissions(self):

        if self.action in ["create", "update", "partial_update", "destroy"]:

            return [IsAuthenticated(), CanManageShopPrices()]

        return [IsAuthenticated()]

    def get_queryset(self):

        user = self.request.user

        base = DistributorPrice.objects.select_related("distributor", "product")

        if _is_staff(user):

            qs = base

            distributor_id = self.request.query_params.get("distributor")

            if distributor_id:

                qs = qs.filter(distributor_id=distributor_id)

            return qs

        if user.role == "DISTRIBUTOR" and hasattr(user, "distributor_profile"):

            return base.filter(distributor=user.distributor_profile)

        if user.role == "CUSTOMER" and hasattr(user, "customer_profile"):

            dist_id = user.customer_profile.distributor_id

            if dist_id:

                return base.filter(distributor_id=dist_id)

        return DistributorPrice.objects.none()

    def perform_create(self, serializer):

        user = self.request.user


        if user.role == "DISTRIBUTOR":


            serializer.save(distributor=user.distributor_profile)


            return



        raw = self.request.data.get("distributor")


        distributor = Distributor.objects.filter(pk=raw).first()


        if not distributor:


            raise ValidationError(
                {"distributor": "شناسه پخش‌کننده الزامی است."}
            )


        serializer.save(distributor=distributor)

    def perform_update(self, serializer):


        user = self.request.user


        if user.role == "DISTRIBUTOR" and \
                serializer.instance.distributor_id != user.distributor_profile_id:


            raise PermissionDenied("فقط فروشگاه خودتان قابل ویرایش است.")


        serializer.save()

    def perform_destroy(self, instance):


        user = self.request.user


        if user.role == "DISTRIBUTOR" and \
                instance.distributor_id != user.distributor_profile_id:


            raise PermissionDenied("فقط فروشگاه خودتان قابل حذف است.")


        instance.delete()


class CanManageShopPrices:

    def has_permission(self, request, view):

        user = request.user

        return bool(
            user.is_authenticated
            and (
                user.is_superuser
                or user.role in ["ADMIN", "SECRETARY", "DISTRIBUTOR"]
            )
        )

    def has_object_permission(self, request, view, obj):

        user = request.user

        if _is_staff(user):

            return True

        return bool(
            user.role == "DISTRIBUTOR"
            and obj.distributor_id == getattr(user, "distributor_profile_id", None)
        )


class LegacyProductPriceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    (منسوخ) دسترسی فقط-خواندنی به مدل قدیمی per-customer
    برای گزارش‌گیری؛ از جریان خرید حذف شده است.
    """

    queryset = ProductPrice.objects.select_related("customer", "product").all()

    serializer_class = ProductPriceSerializer

    permission_classes = [IsAuthenticated]
