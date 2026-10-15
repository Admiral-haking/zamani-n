from unicodedata import normalize as _unicode_normalize

from django.db import transaction, models

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action


from .models import Cart
from .serializers import CartSerializer
from apps.products.models import Product
from apps.common.permissions.customer import IsCustomer
from rest_framework import exceptions



class CartViewSet(viewsets.ModelViewSet):

    serializer_class = CartSerializer

    permission_classes = [IsCustomer]


    def get_queryset(self):

        customer = getattr(self.request.user, "customer_profile", None)
        if customer is None:
            return Cart.objects.none()

        return (
            Cart.objects
            .filter(
                customer=customer
            )
            .order_by("-created_at", "-id")
            .select_related(
                "product"
            )
        )
    def perform_create(self, serializer):

        customer = getattr(self.request.user, "customer_profile", None)
        if customer is None:
            raise exceptions.ValidationError("حساب مشتری برای این کاربر یافت نشد.")

        product = serializer.validated_data["product"]

        quantity = serializer.validated_data["quantity"]


        # افزایش اتمیک تعداد تا از گم شدن آپدیت‌های همزمان
        # (lost update) جلوگیری شود
        with transaction.atomic():

            cart_item, created = Cart.objects.get_or_create(

                customer=customer,

                product=product,

                defaults={

                    "quantity": quantity

                }

            )


            if not created:

                Cart.objects.filter(
                    pk=cart_item.pk
                ).update(
                    quantity=models.F("quantity") + quantity
                )

                cart_item.refresh_from_db()


        serializer.instance = cart_item



    @action(
        detail=False,
        methods=["delete"]
    )
    def clear(self, request):

        Cart.objects.filter(
            customer=getattr(request.user, "customer_profile", None)
        ).delete()


        return Response(
            {
                "message": "Cart cleared"
            }
        )


    @action(
        detail=False,
        methods=["post"]
    )
    def sync(self, request):
        """جایگزینی کامل سبد سرور با سبد محلی.

        هر آیتم می‌تواند `product` (شناسه محصول واقعی)،
        `catalogId` یا نام محصول (`name`) داشته باشد.
        آیتم‌هایی که به محصول فعالی نگاشت نشوند نادیده گرفته می‌شوند.
        """

        customer = getattr(self.request.user, "customer_profile", None)
        if customer is None:
            return Response({"error": "حساب مشتری برای این کاربر یافت نشد."}, status=400)

        items = request.data.get("items") or []

        if not isinstance(items, list):

            return Response(
                {"error": "items must be a list."},
                status=400
            )


        active_products = list(
            Product.objects.filter(is_active=True)
        )

        product_by_id = {
            product.id: product
            for product in active_products
        }

        name_index = {}

        for product in active_products:

            key = _normalize_product_name(product.name)

            name_index.setdefault(key, product)


        aggregates = {}

        for raw in items:

            if not isinstance(raw, dict):
                continue

            try:

                quantity = int(raw.get("quantity") or 1)

            except (TypeError, ValueError):

                quantity = 1

            if quantity <= 0:
                continue

            product = None

            raw_id = raw.get("product") or raw.get(
                "catalog_id") or raw.get("catalogId")

            if raw_id is not None:

                try:

                    raw_id = int(raw_id)

                except (TypeError, ValueError):

                    raw_id = None

                if raw_id is not None:

                    product = product_by_id.get(raw_id)

            if product is None:

                name = raw.get("name") or raw.get("product_name")

                if name:

                    product = name_index.get(
                        _normalize_product_name(name)
                    )

            if product is None:
                continue

            aggregates[product.id] = aggregates.get(
                product.id, 0
            ) + quantity


        with transaction.atomic():

            Cart.objects.filter(
                customer=customer
            ).delete()

            for product_id, quantity in aggregates.items():

                Cart.objects.create(
                    customer=customer,
                    product_id=product_id,
                    quantity=quantity
                )


        serializer = self.get_serializer(
            self.get_queryset(),
            many=True
        )

        return Response(
            {
                "items": serializer.data,
                "synced": len(aggregates) > 0
            }
        )


def _normalize_product_name(value):
    """همان منطق normalizeName در index.html"""

    return (
        _unicode_normalize("NFKC", str(value or ""))
        .replace("٪", "")
        .replace("%", "")
        .replace("ـ", "")
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
        .replace(" ", "")
        .replace("،", "")
        .replace(",", "")
        .lower()
    )
