from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions.permissions import IsAdminOrSecretary
from apps.accounts.models import User
from apps.customers.models import Customer
from apps.tickets.models import Ticket
from apps.audit.services import AuditService


class AccountRequestListView(APIView):
    """لیست تیکت‌های «درخواست ایجاد حساب» برای ادمین کل"""

    permission_classes = [IsAuthenticated, IsAdminOrSecretary]

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

    permission_classes = [IsAuthenticated, IsAdminOrSecretary]

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

        national_id = (request.data.get("national_id") or "").strip() or None
        user = User.objects.create(
            username=username,
            role=User.Role.CUSTOMER,
            phone=ticket.guest_phone or None,
            first_name=(request.data.get("first_name") or ticket.guest_name).strip(),
            last_name=(request.data.get("last_name") or "").strip(),
            national_code=national_id,
        )
        user.set_password(password)
        user.save()

        customer = getattr(user, "customer_profile", None)
        if customer is None:
            customer = Customer(user=user)
        customer.phone = ticket.guest_phone
        customer.company_name = (request.data.get("shop_name") or ticket.guest_name).strip()
        customer.shop_name = (request.data.get("shop_name") or ticket.guest_name).strip()
        customer.national_id = national_id
        customer.postal_code = (request.data.get("postal_code") or "").strip()
        customer.address = (request.data.get("address") or "").strip()
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


class AccountRequestRejectView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSecretary]

    def post(self, request, pk=None):
        ticket = Ticket.objects.filter(
            pk=pk, category=Ticket.Category.ACCOUNT_REQUEST, user__isnull=True
        ).first()
        if not ticket:
            return Response({"error": "درخواست یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        ticket.admin_reply = (request.data.get("note") or "درخواست رد شد.").strip()
        ticket.admin_replied_at = timezone_now()
        ticket.status = Ticket.Status.CLOSED
        ticket.save(update_fields=["admin_reply", "admin_replied_at", "status", "updated_at"])
        return Response({"message": "درخواست رد شد."})


class AccountRequestDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSecretary]

    def delete(self, request, pk=None):
        ticket = Ticket.objects.filter(
            pk=pk, category=Ticket.Category.ACCOUNT_REQUEST, user__isnull=True
        ).first()
        if not ticket:
            return Response({"error": "درخواست یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def timezone_now():
    from django.utils import timezone

    return timezone.now()
