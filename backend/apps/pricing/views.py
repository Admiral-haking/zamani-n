from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated


from .models import ProductPrice

from .serializers import ProductPriceSerializer

from .permissions import CanManagePrice

from .selectors import PricingSelector



class ProductPriceViewSet(viewsets.ModelViewSet):


    serializer_class = ProductPriceSerializer



    def get_permissions(self):


        if self.action in [

            "create",

            "update",

            "partial_update",

            "destroy"

        ]:


            return [

                IsAuthenticated(),

                CanManagePrice()

            ]


        return [

            IsAuthenticated()

        ]




    def get_queryset(self):


        user = self.request.user



        if user.role in [

            "ADMIN",

            "SECRETARY"

        ]:


            return PricingSelector.all_prices()




        if user.role == "DISTRIBUTOR":


            return (

                ProductPrice.objects

                .filter(

                    customer__distributor=

                    user.distributor_profile

                )

                .select_related(

                    "customer",

                    "product"

                )

            )




        if user.role == "CUSTOMER":


            return (

                ProductPrice.objects

                .filter(

                    customer=user.customer_profile

                )

                .select_related(

                    "product"

                )

            )



        return ProductPrice.objects.none()




    def perform_create(self, serializer):


        user = self.request.user



        if user.role == "DISTRIBUTOR":


            customer = serializer.validated_data["customer"]



            if customer.distributor != user.distributor_profile:


                raise PermissionError(

                    "Cannot set price for this customer."

                )



        serializer.save()




    def perform_update(self, serializer):


        self.perform_create(serializer)


        serializer.save()