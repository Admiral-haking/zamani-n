from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DistributorPrice, ProductPrice

from .serializers import (
    DistributorPriceSerializer,
    ProductPriceSerializer,
    CustomerPriceSerializer,
)

from apps.distributors.models import Distributor
from apps.customers.models import Customer
from apps.products.models import Product


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

    @action(detail=False, methods=["post"])
    def bulk(self, request):
        """ثبت/به‌روزرسانی همزمان قیمت چند محصول برای یک پخش‌کننده (فقط منشی/ادمین)."""

        if not _is_staff(request.user):

            raise PermissionDenied("فقط منشی/ادمین می‌توانند قیمت انبوه ثبت کنند.")

        distributor_id = request.data.get("distributor")

        if not distributor_id:

            raise ValidationError(
                {"distributor": "شناسه پخش‌کننده الزامی است."}
            )

        distributor = Distributor.objects.filter(pk=distributor_id).first()

        if not distributor:

            raise ValidationError(
                {"distributor": "پخش‌کننده یافت نشد."}
            )

        prices = request.data.get("prices", [])

        if not isinstance(prices, list):

            raise ValidationError(
                {"prices": "قالب prices باید لیست باشد."}
            )

        created = 0

        updated = 0

        for item in prices:

            if not isinstance(item, dict):

                continue

            product_id = item.get("product") or item.get("product_id")

            price = item.get("price")

            if product_id in (None, "") or price in (None, ""):

                continue

            try:

                product_id = int(product_id)

                price = int(price)

            except (TypeError, ValueError):

                continue

            if price < 0:

                continue

            _, was_created = DistributorPrice.objects.update_or_create(
                distributor=distributor,
                product_id=product_id,
                defaults={"price": price},
            )

            if was_created:

                created += 1

            else:

                updated += 1

        return Response({
            "success": True,
            "created": created,
            "updated": updated,
            "distributor": distributor.id,
        })


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


class CanManageCustomerPrices:

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

        if user.role == "DISTRIBUTOR" and hasattr(user, "distributor_profile"):

            return obj.customer.distributor_id == user.distributor_profile.id

        return False


class CustomerPriceViewSet(viewsets.ModelViewSet):
    """
    قیمت دستی هر مشتری برای هر محصول.

    - DISTRIBUTOR: مشاهده/ثبت/ویرایش/حذف فقط برای مشتریان زیرمجموعه خودش
    - ADMIN/SECRETARY: همه (با فیلتر customer و distributor)
    - CUSTOMER: فقط خواندن قیمت‌های خودش (برای نمایش «قیمت‌های ویژه من»)
    """

    serializer_class = CustomerPriceSerializer

    permission_classes = [IsAuthenticated]

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ["customer", "product"]

    search_fields = ["product__name"]

    ordering_fields = ["price", "updated_at"]

    ordering = ["product__name"]

    def get_permissions(self):

        if self.action in ["create", "update", "partial_update", "destroy"]:

            return [IsAuthenticated(), CanManageCustomerPrices()]

        return [IsAuthenticated()]

    def get_queryset(self):

        user = self.request.user

        base = ProductPrice.objects.select_related(
            "customer", "customer__user", "product"
        )

        if _is_staff(user):

            qs = base

            customer_id = self.request.query_params.get("customer")

            if customer_id:

                qs = qs.filter(customer_id=customer_id)

            distributor_id = self.request.query_params.get("distributor")

            if distributor_id:

                qs = qs.filter(customer__distributor_id=distributor_id)

            return qs

        if user.role == "DISTRIBUTOR" and hasattr(user, "distributor_profile"):

            return base.filter(customer__distributor=user.distributor_profile)

        if user.role == "CUSTOMER" and hasattr(user, "customer_profile"):

            return base.filter(customer=user.customer_profile)

        return ProductPrice.objects.none()

    def _customer_in_scope(self, customer_id):

        try:

            customer = Customer.objects.select_related("distributor").get(
                pk=customer_id
            )

        except (Customer.DoesNotExist, ValueError, TypeError):

            return None

        user = self.request.user

        if _is_staff(user):

            return customer

        if user.role == "DISTRIBUTOR" and hasattr(user, "distributor_profile"):

            if customer.distributor_id == user.distributor_profile.id:

                return customer

        return None

    def _resolve_product(self, product_id):

        try:

            product = Product.objects.filter(pk=int(product_id)).first()

        except (ValueError, TypeError):

            product = None

        if not product:

            raise ValidationError({"product": "محصول یافت نشد."})

        if not product.is_active:

            raise ValidationError({"product": "محصول غیرفعال است."})

        return product

    @staticmethod
    def _resolve_price(raw):

        try:

            price = int(raw)

        except (TypeError, ValueError):

            raise ValidationError({"price": "قیمت معتبر وارد کنید."})

        if price <= 0:

            raise ValidationError({"price": "قیمت باید بزرگ‌تر از صفر باشد."})

        return price

    def create(self, request, *args, **kwargs):
        """ثبت قیمت دستی (upsert: اگر بود به‌روزرسانی می‌شود)."""

        customer = self._customer_in_scope(request.data.get("customer"))

        if customer is None:

            return Response(
                {"error": "مشتری معتبر برای ثبت قیمت یافت نشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = self._resolve_product(request.data.get("product"))

        price = self._resolve_price(request.data.get("price"))

        obj, _ = ProductPrice.objects.update_or_create(
            customer=customer,
            product=product,
            defaults={"price": price},
        )

        return Response(
            self.get_serializer(obj).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):

        serializer.validated_data.pop("customer", None)
        serializer.validated_data.pop("product", None)
        serializer.save()


class LegacyProductPriceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    (منسوخ) دسترسی فقط-خواندنی به مدل قدیمی per-customer
    برای گزارش‌گیری؛ از جریان خرید حذف شده است.
    """

    queryset = ProductPrice.objects.select_related("customer", "product").all()

    serializer_class = ProductPriceSerializer

    permission_classes = [IsAuthenticated]
