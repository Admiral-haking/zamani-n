from rest_framework import status
from rest_framework import viewsets

from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend


from .models import Customer

from .serializers import CustomerSerializer


from apps.audit.services import AuditService


from apps.common.permissions.permissions import (
    IsAdminOrSecretary,
    IsDistributor
)




class CustomerViewSet(viewsets.ModelViewSet):


    serializer_class = CustomerSerializer



    filter_backends = [

        DjangoFilterBackend,

        SearchFilter,

        OrderingFilter,

    ]



    filterset_fields = [

        "is_active",

    ]



    search_fields = [

        "customer_code",

        "company_name",

        "phone",

        "user__username",

    ]



    ordering_fields = [

        "customer_code",

        "company_name",

        "created_at",

        "account_balance",

    ]



    ordering = [

        "-created_at"

    ]




    def get_queryset(self):


        user = self.request.user



        if user.is_superuser:

            return Customer.objects.all()



        if user.role in [

            "ADMIN",

            "SECRETARY"

        ]:

            return (

                Customer.objects

                .select_related(
                    "user",
                    "distributor"
                )

                .all()

            )




        if user.role == "DISTRIBUTOR":


            return (

                Customer.objects

                .filter(
                    distributor__user=user
                )

                .select_related(
                    "user"
                )

            )




        if user.role == "CUSTOMER":


            return Customer.objects.filter(

                user=user

            )



        return Customer.objects.none()




    def get_permissions(self):


        if self.action in [

            "create",

            "update",

            "partial_update",

            "destroy"

        ]:


            return [

                IsAdminOrSecretary()

            ]



        return [

            IsAuthenticated()

        ]




    def perform_create(self, serializer):


        user = self.request.user



        if user.role == "DISTRIBUTOR":


            customer = serializer.save(

                distributor=user.distributor_profile

            )


        else:


            customer = serializer.save()



        AuditService.log(

            user=user,

            action="CREATE",

            model_name="Customer",

            object_id=customer.id,

            description=f"Customer {customer.customer_code} created"

        )




    def perform_update(self, serializer):


        customer = serializer.save()



        AuditService.log(

            user=self.request.user,

            action="UPDATE",

            model_name="Customer",

            object_id=customer.id,

            description=f"Customer {customer.customer_code} updated"

        )




    def perform_destroy(self, instance):


        code = instance.customer_code

        pk = instance.id



        instance.soft_delete()



        AuditService.log(

            user=self.request.user,

            action="DELETE",

            model_name="Customer",

            object_id=pk,

            description=f"Customer {code} deleted"

        )




    def destroy(self, request, *args, **kwargs):


        instance = self.get_object()



        self.perform_destroy(

            instance

        )



        return Response(

            {

                "success": True,

                "message": "Customer deleted successfully."

            },

            status=status.HTTP_200_OK

        )