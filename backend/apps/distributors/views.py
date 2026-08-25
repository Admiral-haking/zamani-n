from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView

from rest_framework.response import Response


from apps.common.permissions.distributor_access import (
    IsDistributorOrAdminSecretary
)


from .models import Distributor

from .serializers import DistributorSerializer

from .services import DistributorService


from apps.customers.models import Customer

from apps.customers.distributor_serializers import (
    DistributorCustomerSerializer
)



class DistributorViewSet(viewsets.ModelViewSet):


    serializer_class = DistributorSerializer


    permission_classes = [

        IsDistributorOrAdminSecretary

    ]



    def get_queryset(self):


        user = self.request.user



        if user.role in [

            "ADMIN",

            "SECRETARY"

        ]:

            return Distributor.objects.all()



        if user.role == "DISTRIBUTOR":


            return Distributor.objects.filter(

                user=user

            )



        return Distributor.objects.none()





class DistributorDashboardView(APIView):


    permission_classes = [

        IsAuthenticated

    ]



    def get(self, request):


        user = request.user



        if user.role != "DISTRIBUTOR":

            return Response(

                {
                    "detail": "You are not a distributor."
                },

                status=403

            )



        distributor = user.distributor_profile



        return Response(

            {

                "distributor":

                    distributor.full_name,


                "customer_count":

                    DistributorService.customer_count(

                        distributor

                    ),



                "order_count":

                    DistributorService.order_count(

                        distributor

                    ),



                "total_sales":

                    DistributorService.total_sales(

                        distributor

                    )

            }

        )






class DistributorCustomerViewSet(viewsets.ModelViewSet):


    serializer_class = DistributorCustomerSerializer



    permission_classes = [

        IsDistributorOrAdminSecretary

    ]



    def get_queryset(self):


        user = self.request.user



        if user.role in [

            "ADMIN",

            "SECRETARY"

        ]:

            return Customer.objects.all()



        if user.role == "DISTRIBUTOR":


            return Customer.objects.filter(

                distributor=user.distributor_profile

            )



        return Customer.objects.none()


    def perform_create(self, serializer):


        user = self.request.user



        if user.role == "DISTRIBUTOR":


            serializer.save(
                distributor=user.distributor_profile
            )

        elif user.is_superuser or user.role in ["ADMIN", "SECRETARY"]:

            from apps.distributors.models import Distributor

            distributor_id = self.request.data.get("distributor_id")

            if not distributor_id:

                raise PermissionError(

                    "برای ساخت مشتری، شناسه پخش‌کننده معرف الزامی است."

                )

            distributor = Distributor.objects.filter(pk=distributor_id).first()

            if not distributor:

                raise PermissionError("پخش‌کننده یافت نشد.")

            serializer.save(distributor=distributor)

        else:


            raise PermissionError(

                "Only distributors can create customers."

            )