from django.db import transaction as db_transaction

from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import action

from rest_framework.response import Response

from rest_framework import status

from .models import Payment

from .serializers import PaymentSerializer


from apps.finance.services import FinanceService


from apps.audit.services import AuditService


from apps.common.permissions.permissions import IsAdminOrSecretary

from apps.common.permissions.payment import (
    CanManagePayment
)



class PaymentViewSet(viewsets.ModelViewSet):


    serializer_class = PaymentSerializer


    permission_classes = [

        CanManagePayment

    ]



    def get_permissions(self):


        # تایید رسید پرداخت فقط توسط ادمین و منشی انجام می‌شود

        if self.action == "approve":


            return [

                IsAuthenticated(),

                IsAdminOrSecretary(),

            ]



        return [CanManagePayment()]



    def get_queryset(self):


        user = self.request.user



        if user.role in [

            "ADMIN",

            "SECRETARY"

        ]:

            return Payment.objects.select_related(

                "order__customer__user"

            ).all()



        if user.role == "CUSTOMER":


            return Payment.objects.filter(


                order__customer=user.customer_profile


            )



        return Payment.objects.none()




    def _process_success(self, payment):


        """ثبت اثر مالی پرداخت موفق: کاهش بدهی مشتری و علامت‌گذاری پردازش"""


        customer = payment.order.customer


        FinanceService.add_payment(


            customer,


            payment.amount,


            f"Payment #{payment.id}"


        )


        payment.finance_processed = True


        payment.save(


            update_fields=[


                "finance_processed"


            ]


        )




    def perform_create(self, serializer):


        payment = serializer.save()



        if (


            payment.status == Payment.Status.SUCCESS


            and not payment.finance_processed


        ):


            self._process_success(payment)


            AuditService.log(


                user=self.request.user,


                action="CREATE",


                model_name="Payment",


                object_id=payment.id,


                description=(


                    f"Payment #{payment.id} ({payment.amount}) "


                    f"created as SUCCESS by {self.request.user.username}"


                ),


            )



    @action(detail=True, methods=["post"])

    def approve(self, request, pk=None):


        """تایید رسید پرداخت توسط منشی/ادمین و تسویه خودکار حساب مشتری"""


        # قفل ردیف پرداخت تا دو تایید همزمان فقط یکبار اجرا شود

        with db_transaction.atomic():

            payment = Payment.objects.select_for_update().get(
                pk=self.get_object().pk
            )

            if payment.status == Payment.Status.SUCCESS:

                return Response(


                    {"error": "این پرداخت قبلاً تایید شده است."},


                    status=status.HTTP_400_BAD_REQUEST,


                )



            if payment.status == Payment.Status.FAILED:


                return Response(


                    {"error": "پرداخت ناموفق قابل تایید نیست."},


                    status=status.HTTP_400_BAD_REQUEST,


                )



            old_status = payment.status


            payment.status = Payment.Status.SUCCESS


            payment.save(update_fields=["status"])



            if not payment.finance_processed:


                self._process_success(payment)



        AuditService.log(


            user=request.user,


            action="APPROVE",


            model_name="Payment",


            object_id=payment.id,


            description=(


                f"Payment #{payment.id} ({payment.amount}) "


                f"approved by {request.user.username} "


                f"[{old_status} -> {Payment.Status.SUCCESS}]"


            ),


        )



        serializer = self.get_serializer(payment)


        return Response(serializer.data)
