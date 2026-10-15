from django.db import transaction as db_transaction

from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import action, api_view

from rest_framework.response import Response

from rest_framework import status

from rest_framework.permissions import AllowAny

from rest_framework.decorators import permission_classes

from django.http import HttpResponse

from .models import Payment

from .serializers import PaymentSerializer

from .services import ZarinpalService


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
        if not user.is_authenticated:
            return Payment.objects.none()


        if user.role in [

            "ADMIN",

            "SECRETARY"

        ]:

            return Payment.objects.select_related(

                "order__customer__user"

            ).order_by("-created_at", "-id")



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


            f"Payment #{payment.id}",


            payment=payment


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


    @action(detail=True, methods=["post"])

    def init_online(self, request, pk=None):

        """ایجاد لینک پرداخت آنلاین زرین‌پال برای یک پرداخت در انتظار"""

        payment = self.get_object()


        if payment.method != Payment.Method.ONLINE:

            return Response(

                {"error": "این پرداخت از نوع آنلاین نیست."},

                status=status.HTTP_400_BAD_REQUEST,

            )


        if payment.status != Payment.Status.PENDING:

            return Response(

                {"error": "فقط پرداخت‌های در انتظار قابل پرداخت آنلاین هستند."},

                status=status.HTTP_400_BAD_REQUEST,

            )


        order = payment.order

        customer = order.customer

        email = getattr(getattr(customer, "user", None), "email", None)

        mobile = getattr(customer, "phone", None)


        authority, url_or_error = ZarinpalService.request_payment(

            payment.amount,

            f"فاکتور #{order.id} - {order.tracking_code or ''}",

            email=email,

            mobile=mobile,

        )


        if not authority:

            return Response(

                {"error": url_or_error or "خطا در ایجاد لینک پرداخت"},

                status=status.HTTP_502_BAD_GATEWAY,

            )


        payment.reference_number = authority

        payment.save(update_fields=["reference_number"])

        AuditService.log(

            user=request.user,

            action="INIT_PAYMENT",

            model_name="Payment",

            object_id=payment.id,

            description=f"Online payment #{payment.id} ({payment.amount}) initiated by {request.user.username}",

        )


        return Response({"authority": authority, "payment_url": url_or_error})



@api_view(["GET"])

@permission_classes([AllowAny])

def zarinpal_callback(request):

    """بازگشت کاربر پس از پرداخت از درگاه زرین‌پال (نقطه فراخوانی عمومی)"""

    authority = request.query_params.get("Authority") or request.query_params.get("authority")

    pay_status = request.query_params.get("Status") or request.query_params.get("status")


    def _html(title, message, ok, qs=""):

        btn_text = "بازگشت به حساب کاربری"

        color = "#2ecc71" if ok else "#e74c3c"

        target = "dashbord.html" + (("?" + qs) if qs else "")

        page = f"""

<html dir="rtl" lang="fa">

<head><meta charset="utf-8"><title>{title}</title>

<meta name="viewport" content="width=device-width, initial-scale=1">

</head>

<body style="font-family:Tahoma,sans-serif;background:#f4f4f6;margin:0;padding:0;">

<div style="max-width:460px;margin:60px auto;background:#fff;border-radius:16px;padding:32px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,.12);">

<div style="font-size:56px;">{"✅" if ok else "❌"}</div>

<h2 style="color:{color};margin:12px 0;">{title}</h2>

<p style="color:#555;line-height:2;">{message}</p>

<a href="{target}" style="display:inline-block;margin-top:18px;padding:12px 28px;border-radius:10px;background:#d4a017;color:#111;text-decoration:none;font-weight:bold;">{btn_text}</a>

</div>

<script>setTimeout(function(){{ window.location.href = '{target}'; }}, 5000);</script>

</body>

</html>

"""

        return HttpResponse(page)


    if not authority:

        return _html("خطا", "درخواست بازگشت از درگاه معتبر نیست.", False, "pay=error")


    payment = Payment.objects.select_related("order__customer__user").filter(

        method=Payment.Method.ONLINE,

        status=Payment.Status.PENDING,

        reference_number=authority,

    ).first()


    if not payment:

        return _html("خطا", "پرداخت یافت نشد یا قبلاً پردازش شده است.", False, "pay=error")


    order = payment.order


    if str(pay_status).lower() == "ok":

        success, ref_id, message = ZarinpalService.verify_payment(authority, payment.amount)

        if success:

            with db_transaction.atomic():

                payment.status = Payment.Status.SUCCESS

                payment.reference_number = ref_id or payment.reference_number

                payment.save(update_fields=["status", "reference_number"])

                if not payment.finance_processed:

                    customer = order.customer

                    FinanceService.add_payment(customer, payment.amount, f"Payment #{payment.id}", payment=payment)

                    payment.finance_processed = True

                    payment.save(update_fields=["finance_processed"])

                if order.status == "PENDING":

                    order.status = "CONFIRMED"

                    order.save(update_fields=["status"])

            AuditService.log(

                user=None,

                action="PAY_SUCCESS",

                model_name="Payment",

                object_id=payment.id,

                description=f"Online payment #{payment.id} ({payment.amount}) verified via Zarinpal. Ref: {ref_id}",

            )

            return _html("پرداخت موفق", f"پرداخت شما با موفقیت انجام شد.<br>شناسه پیگیری درگاه: {ref_id}<br>کد پیگیری سفارش: {order.tracking_code or '-'}", True, "pay=success")

        return _html("پرداخت ناموفق", f"پرداخت شما قابل تأیید نیست. {message or ''}", False, "pay=failed")

    else:

        payment.status = Payment.Status.FAILED

        payment.save(update_fields=["status"])

        AuditService.log(

            user=None,

            action="PAY_FAILED",

            model_name="Payment",

            object_id=payment.id,

            description=f"Online payment #{payment.id} failed at gateway.",

        )

        return _html("پرداخت لغو شد", "کاربر از ادامه پرداخت انصراف داد یا پرداخت ناموفق بود.", False, "pay=cancelled")
