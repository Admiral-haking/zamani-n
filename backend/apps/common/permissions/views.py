from rest_framework import viewsets

from rest_framework.decorators import action

from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from django.db import models


from apps.inventory.models import Inventory

from .serializers.inventory_serializer import InventorySerializer


from apps.common.permissions.inventory import (
    CanManageInventory
)




class InventoryViewSet(viewsets.ModelViewSet):


    queryset = (

        Inventory.objects

        .select_related(
            "product"
        )

        .all()

    )


    serializer_class = InventorySerializer



    def get_permissions(self):


        if self.action in [

            "increase",

            "decrease",

            "create",

            "update",

            "partial_update",

            "destroy",

            "low_stock"

        ]:


            return [

                CanManageInventory()

            ]



        return [

            IsAuthenticated()

        ]




    @action(
        detail=True,
        methods=["post"]
    )
    def increase(self, request, pk=None):


        inventory = self.get_object()



        amount = int(

            request.data.get(
                "amount",
                0
            )

        )



        if amount <= 0:

            return Response(

                {
                    "error":
                    "Amount must be positive"
                },

                status=400

            )



        inventory.quantity += amount

        inventory.save()



        return Response(

            {
                "message":
                "Stock increased",

                "quantity":
                inventory.quantity

            }

        )




    @action(
        detail=True,
        methods=["post"]
    )
    def decrease(self, request, pk=None):


        inventory = self.get_object()



        amount = int(

            request.data.get(
                "amount",
                0
            )

        )



        if amount <= 0:

            return Response(

                {
                    "error":
                    "Amount must be positive"
                },

                status=400

            )



        if inventory.quantity < amount:


            return Response(

                {
                    "error":
                    "Not enough stock"
                },

                status=400

            )



        inventory.quantity -= amount

        inventory.save()



        return Response(

            {
                "message":
                "Stock decreased",

                "quantity":
                inventory.quantity

            }

        )




    @action(
        detail=False,
        methods=["get"]
    )
    def low_stock(self, request):


        items = Inventory.objects.filter(

            quantity__lte=models.F(
                "minimum_stock"
            )

        )



        serializer = self.get_serializer(

            items,

            many=True

        )



        return Response(

            serializer.data

        )