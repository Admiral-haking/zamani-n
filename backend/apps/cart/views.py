from django.db import transaction, models

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action


from .models import Cart
from .serializers import CartSerializer



class CartViewSet(viewsets.ModelViewSet):

    serializer_class = CartSerializer

    permission_classes = [
        IsAuthenticated
    ]


    def get_queryset(self):

        customer = self.request.user.customer_profile

        return (
            Cart.objects
            .filter(
                customer=customer
            )
            .select_related(
                "product"
            )
        )
    def perform_create(self, serializer):

        customer = self.request.user.customer_profile

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
            customer=request.user.customer_profile
        ).delete()


        return Response(
            {
                "message": "Cart cleared"
            }
        )