from rest_framework import viewsets, status

from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView

from rest_framework.response import Response

from rest_framework.decorators import action

from django.db.models import Sum, Count, Q, Value, DecimalField

from django.db.models.functions import Coalesce, TruncDate

from decimal import Decimal

from datetime import timedelta


from apps.common.permissions.distributor_access import (
    IsDistributorOrAdminSecretary
)


from .models import Distributor, DistributorPurchase

from .serializers import DistributorSerializer, DistributorPurchaseSerializer

from .services import DistributorService


from apps.customers.models import Customer

from apps.customers.distributor_serializers import (
    DistributorCustomerSerializer
)

from apps.tickets.models import Ticket



class DistributorViewSet(viewsets.ModelViewSet):


    serializer_class = DistributorSerializer


    search_fields = (
        "full_name",
        "phone",
        "city",
    )


    permission_classes = [

        IsDistributorOrAdminSecretary

    ]



    def get_queryset(self):


        user = self.request.user
        if not user.is_authenticated:
            return Distributor.objects.none()



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

    def perform_destroy(self, instance):
        user = instance.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        super().perform_destroy(instance)



class DistributorDashboardView(APIView):


    permission_classes = [

        IsAuthenticated

    ]


    SALES_STATUSES = ("CONFIRMED", "PREPARING", "SHIPPED", "DELIVERED")

    FA_MONTHS = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]

    FA_DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]

    @staticmethod
    def _fa_digits(value):
        return "".join(
            "۰۱۲۳۴۵۶۷۸۹"[int(ch)] if ch.isdigit() else ch
            for ch in str(value)
        )

    @staticmethod
    def _to_jalali(gy, gm, gd):
        """تبدیل تاریخ میلادی به شمسی (الگوریتم استاندارد، بدون وابستگی خارجی)"""
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        if gm > 2:
            gy2 = gy + 1
        else:
            gy2 = gy
        days = (
            355666
            + 365 * gy
            + (gy2 + 3) // 4
            - (gy2 + 99) // 100
            + (gy2 + 399) // 400
            + gd
            + g_d_m[gm - 1]
        )
        jy = -1595 + 33 * (days // 12053)
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461
        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365
        if days < 186:
            jm = 1 + days // 31
            jd = 1 + days % 31
        else:
            jm = 7 + (days - 186) // 30
            jd = 1 + (days - 186) % 30
        return jy, jm, jd

    def _chart_data(self, orders_qs, period):
        """نمودار فروش بر اساس بازه: daily (۷ روز) / weekly (۸ هفته) / monthly (۶ ماه) / yearly (۵ سال)"""
        from datetime import date as _date, timedelta as _td

        _today = _date.today()
        sales = orders_qs.filter(status__in=self.SALES_STATUSES)

        if period == "weekly":
            items = []
            for i in range(7, -1, -1):
                ref = _today - _td(weeks=i)
                start = ref - _td(days=ref.weekday())
                end = start + _td(days=6)
                total = sales.filter(
                    created_at__date__gte=start,
                    created_at__date__lte=min(end, _today),
                ).aggregate(total=Sum("total_price"))["total"] or 0
                jy, jm, jd = self._to_jalali(start.year, start.month, start.day)
                items.append({
                    "label": f"{self._fa_digits(jd)} {self.FA_MONTHS[jm - 1]}",
                    "date": start.strftime("%Y-%m-%d"),
                    "total": int(total),
                    "count": sales.filter(
                        created_at__date__gte=start,
                        created_at__date__lte=min(end, _today),
                    ).count(),
                })
            return items

        if period == "monthly":
            items = []
            y, m = _today.year, _today.month
            for _ in range(6):
                total = sales.filter(
                    created_at__date__year=y,
                    created_at__date__month=m,
                ).aggregate(total=Sum("total_price"))["total"] or 0
                jy, jm, _ = self._to_jalali(y, m, 15)
                items.append({
                    "label": f"{self.FA_MONTHS[jm - 1]} {self._fa_digits(jy)}",
                    "date": f"{y:04d}-{m:02d}-01",
                    "total": int(total),
                    "count": sales.filter(
                        created_at__date__year=y,
                        created_at__date__month=m,
                    ).count(),
                })
                m -= 1
                if m < 1:
                    m = 12
                    y -= 1
            items.reverse()
            return items

        if period == "yearly":
            items = []
            for y in range(_today.year - 4, _today.year + 1):
                total = sales.filter(
                    created_at__date__year=y,
                ).aggregate(total=Sum("total_price"))["total"] or 0
                jy, _, _ = self._to_jalali(y, 6, 15)
                items.append({
                    "label": self._fa_digits(jy),
                    "date": f"{y:04d}-01-01",
                    "total": int(total),
                    "count": sales.filter(created_at__date__year=y).count(),
                })
            return items

        # daily: فروش ۷ روز اخیر (رفتار قبلی بدون تغییر)
        chart_rows = (
            sales
            .filter(created_at__date__gte=_today - _td(days=6))
            .annotate(d=TruncDate("created_at"))
            .values("d")
            .annotate(t=Sum("total_price"), c=Count("id"))
        )
        chart_map = {}
        for row in chart_rows:
            if row["d"] is not None:
                chart_map[row["d"]] = {
                    "total": int(row["t"] or 0),
                    "count": row["c"],
                }
        chart_data = []
        for i in range(6, -1, -1):
            d = _today - _td(days=i)
            item = chart_map.get(d, {"total": 0, "count": 0})
            item["label"] = self.FA_DAYS[(d.isoweekday() + 1) % 7]
            item["date"] = d.strftime("%Y-%m-%d")
            chart_data.append(item)
        return chart_data


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

        orders_qs = DistributorService.get_orders(distributor)

        from datetime import date as _date, timedelta as _td

        from django.db.models import Sum as _Sum

        _today = _date.today()

        week_start = _today - _td(days=_today.weekday())

        month_start = _today.replace(day=1)

        def _sum_range(start):

            total = orders_qs.filter(
                status__in=self.SALES_STATUSES,
                created_at__date__gte=start,
                created_at__date__lte=_today
            ).aggregate(total=_Sum("total_price"))["total"] or 0

            return int(total)

        # نمودار فروش بر اساس بازه درخواستی (پیش‌فرض: ۷ روز اخیر)
        period = (request.query_params.get("period") or "daily").strip().lower()
        if period not in ("daily", "weekly", "monthly", "yearly"):
            period = "daily"
        chart_data = self._chart_data(orders_qs, period)

        customers = DistributorService.get_customers(distributor)

        customer_user_ids = list(customers.values_list("user_id", flat=True))

        new_tickets = Ticket.objects.filter(
            user_id__in=customer_user_ids,
            status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]
        ).count()

        debtor_balance = customers.filter(
            account_balance__gt=0
        ).aggregate(total=_Sum("account_balance"))["total"] or 0

        debt_to_company = DistributorPurchase.objects.filter(
            distributor=distributor,
            status__in=[
                DistributorPurchase.Status.PENDING,
                DistributorPurchase.Status.CONFIRMED
            ]
        ).aggregate(total=_Sum("total_amount"))["total"] or 0

        distributor_data = DistributorSerializer(distributor).data

        distributor_data["username"] = distributor.user.username

        distributor_data["email"] = distributor.user.email or ""

        return Response(

            {

                "distributor": distributor_data,

                "customer_count":

                    DistributorService.customer_count(

                        distributor

                    ),

                "order_count":

                    DistributorService.order_count(

                        distributor

                    ),

                "total_sales": int(DistributorService.total_sales(distributor)),

                "today_sales": _sum_range(_today),

                "week_sales": _sum_range(week_start),

                "month_sales": _sum_range(month_start),

                "orders_today": orders_qs.filter(
                    created_at__date=_today
                ).count(),

                "new_tickets": new_tickets,

                "debtor_balance": int(debtor_balance),

                "debt_to_company": int(debt_to_company),

                "chart_data": chart_data,

                "chart_period": period,

            }

        )




class DistributorPurchaseViewSet(viewsets.ModelViewSet):


    serializer_class = DistributorPurchaseSerializer


    permission_classes = [

        IsAuthenticated

    ]


    http_method_names = ["get", "post", "head", "options"]


    def get_permissions(self):

        if self.action in ["confirm", "reject"]:

            return [IsDistributorOrAdminSecretary()]

        return [IsAuthenticated()]


    def get_queryset(self):

        user = self.request.user
        if not user.is_authenticated:
            return DistributorPurchase.objects.none()

        if user.role in ["ADMIN", "SECRETARY"]:

            return DistributorPurchase.objects.select_related(
                "distributor"
            ).all()

        if user.role == "DISTRIBUTOR":

            return DistributorPurchase.objects.filter(
                distributor=user.distributor_profile
            ).select_related("distributor")

        return DistributorPurchase.objects.none()


    def perform_create(self, serializer):

        user = self.request.user

        if user.role != "DISTRIBUTOR":

            raise PermissionError("فقط پخش‌کننده می‌تواند خرید ثبت کند.")

        serializer.save(distributor=user.distributor_profile)


    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):

        purchase = self.get_object()

        user = request.user

        is_owner = (
            user.role == "DISTRIBUTOR"
            and purchase.distributor.user_id == user.id
        )

        if not (is_owner or user.role in ["ADMIN", "SECRETARY"]):

            return Response(
                {"error": "اجازه لغو این خرید را ندارید."},
                status=status.HTTP_403_FORBIDDEN
            )

        if purchase.status != DistributorPurchase.Status.PENDING:

            return Response(
                {"error": "فقط خریدهای در انتظار تایید قابل لغو هستند."},
                status=status.HTTP_400_BAD_REQUEST
            )

        purchase.status = DistributorPurchase.Status.CANCELLED

        purchase.save()

        return Response(self.get_serializer(purchase).data)


    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):

        purchase = self.get_object()

        if request.user.role not in ["ADMIN", "SECRETARY"]:

            return Response(
                {"error": "فقط منشی/ادمین می‌تواند خرید را تایید کند."},
                status=status.HTTP_403_FORBIDDEN
            )

        if purchase.status != DistributorPurchase.Status.PENDING:

            return Response(
                {"error": "فقط خریدهای در انتظار تایید قابل تایید هستند."},
                status=status.HTTP_400_BAD_REQUEST
            )

        purchase.status = DistributorPurchase.Status.CONFIRMED

        purchase.save()

        return Response(self.get_serializer(purchase).data)


    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):

        purchase = self.get_object()

        if request.user.role not in ["ADMIN", "SECRETARY"]:

            return Response(
                {"error": "فقط منشی/ادمین می‌تواند خرید را رد کند."},
                status=status.HTTP_403_FORBIDDEN
            )

        if purchase.status != DistributorPurchase.Status.PENDING:

            return Response(
                {"error": "فقط خریدهای در انتظار تایید قابل رد هستند."},
                status=status.HTTP_400_BAD_REQUEST
            )

        purchase.status = DistributorPurchase.Status.REJECTED

        purchase.save()

        return Response(self.get_serializer(purchase).data)






class DistributorCustomerViewSet(viewsets.ModelViewSet):


    serializer_class = DistributorCustomerSerializer



    permission_classes = [

        IsDistributorOrAdminSecretary

    ]



    def get_queryset(self):


        user = self.request.user
        if not user.is_authenticated:
            return Customer.objects.none()


        qs = Customer.objects.annotate(
            orders_count=Count("orders", distinct=True),
            purchased_total=Coalesce(
                Sum("orders__total_price"),
                Value(Decimal("0")),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        ).order_by("-created_at")



        if user.role in [

            "ADMIN",

            "SECRETARY"

        ]:

            return qs



        if user.role == "DISTRIBUTOR":


            return qs.filter(

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
