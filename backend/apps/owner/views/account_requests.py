from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.owner.permissions import IsOwner
from apps.accounts.models import User
from apps.customers.models import Customer
from apps.tickets.models import Ticket
from apps.audit.services import AuditService


class AccountRequestListView(APIView):
    """لیست تیکت‌های «درخواست ایجاد حساب» برای ادمین کل"""

    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        qs = Ticket.objects.filter(
            category=Ticket.Category.ACCOUNT_REQUEST,
            user__isnull=True,
        ).exclude(status=Ticket.Status.CLOSED).order_by("-created_at")

        data = [
            {
                "id": t.id,
                "guest_name": t.guest_name,
                "guest_phone": t.guest_phone,
                "message": t.message,
                "status": t.status,
                "created_at": t.created_at,
            }
            for t in qs
        ]
        return Response({"count": len(data), "requests": data})


class AccountRequestApproveView(APIView):
    """
    تایید درخواست حساب توسط ادمین کل:
    مشتری جدید زیرمجموعه خودِ ادمین کل (بدون معرف) ساخته می‌شود.
    """

    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, pk=None):
        ticket = Ticket.objects.filter(
            pk=pk,
            category=Ticket.Category.ACCOUNT_REQUEST,
            user__isnull=True,
        ).first()
        if not ticket:
            return Response(
                {"error": "درخواست یافت نشد."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if ticket.status == Ticket.Status.CLOSED:
            return Response(
                {"error": "این درخواست قبلاً نهایی شده است."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.data.get("username") or f"user{ticket.guest_phone[-6:]}"
        password = request.data.get("password")
        if not password or len(password) < 8:
            return Response(
                {"error": "رمز عبور الزامی است (حداقل ۸ کاراکتر)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "این نام کاربری قبلاً گرفته شده است."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create(
            username=username,
            role=User.Role.CUSTOMER,
            phone=ticket.guest_phone or None,
        )
        user.set_password(password)
        user.save()

        customer = getattr(user, "customer_profile", None)
        if customer is None:
            customer = Customer(user=user)
        customer.phone = ticket.guest_phone
        customer.company_name = ticket.guest_name
        customer.distributor = None  # زیرمجموعه ادمین کل
        customer.save()

        ticket.admin_reply = (
            f"Account created: {username} (under super admin)"
        )
        ticket.admin_replied_at = timezone_now()
        ticket.status = Ticket.Status.CLOSED
        ticket.save()

        AuditService.log(
            user=request.user,
            action="APPROVE",
            model_name="Ticket",
            object_id=ticket.id,
            description=(
                f"Guest account request #{ticket.id} approved; "
                f"customer '{username}' created under admin"
            ),
        )

        return Response({
            "ticket": ticket.id,
            "user": {"id": user.id, "username": username},
            "message": "حساب مشتری زیرمجموعه ادمین کل ساخته شد.",
        })


def timezone_now():
    from django.utils import timezone

    return timezone.now()
