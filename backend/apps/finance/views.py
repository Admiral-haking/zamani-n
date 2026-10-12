# backend/apps/finance/views.py
from rest_framework import viewsets, status, exceptions
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from collections import OrderedDict

from .models import Transaction, Check
from .serializers import (
    TransactionSerializer,
    CheckSerializer
)
from apps.audit.services import AuditService
from apps.common.permissions.permissions import IsAdminOrSecretary
from apps.common.permissions.distributor_access import IsDistributorOrAdminSecretary
from apps.finance.services import FinanceService
from apps.customers.models import Customer
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.distributors.models import Distributor
from apps.tickets.models import Ticket

# فاکتورهایی که فروش محسوب می‌شوند (خریدهای واقعی مشتری)
SALES_STATUSES = ('CONFIRMED', 'PREPARING', 'SHIPPED', 'DELIVERED')


class TransactionViewSet(viewsets.ModelViewSet):
    """
    مدیریت کامل تراکنش‌های مالی
    """
    
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'customer__id']
    search_fields = ['description', 'customer__company_name', 'customer__phone']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrSecretary()]
        if self.action in ['summary', 'debtors']:
            # پخش‌کننده هم خلاصه مالی/بدهکاران را می‌بیند ولی فقط برای مشتریان خودش
            return [IsDistributorOrAdminSecretary()]
        return [IsAuthenticated()]

    @staticmethod
    def _distributor_profile(user):
        if user.role == 'DISTRIBUTOR':
            return getattr(user, 'distributor_profile', None)
        return None

    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['ADMIN', 'SECRETARY']:
            return Transaction.objects.select_related('customer', 'user', 'payment', 'order').prefetch_related('order__items__product').all()
        
        if user.role == 'DISTRIBUTOR':
            return Transaction.objects.filter(
                customer__distributor__user=user
            ).select_related('customer', 'user', 'payment', 'order').prefetch_related('order__items__product')
        
        if user.role == 'CUSTOMER':
            return Transaction.objects.filter(
                customer__user=user
            ).select_related('customer', 'user', 'payment', 'order').prefetch_related('order__items__product')
        
        return Transaction.objects.none()

    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)
        AuditService.log(
            user=self.request.user,
            action="CREATE",
            model_name="Transaction",
            object_id=transaction.id,
            description=f"Transaction #{transaction.id} created by {self.request.user.username}"
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """تراکنش‌های امروز"""
        today = datetime.now().date()
        transactions = self.get_queryset().filter(created_at__date=today)
        total = transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        # تفکیک بر اساس نوع تراکنش (مبلغ تراکنش‌ها همیشه مثبت ذخیره می‌شوند)
        income = transactions.filter(
            transaction_type__in=[Transaction.Type.PAYMENT, Transaction.Type.RETURN]
        ).aggregate(total=Sum('amount'))['total'] or 0
        expense = transactions.filter(
            transaction_type=Transaction.Type.ORDER_DEBT
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        serializer = self.get_serializer(transactions, many=True)
        return Response({
            'count': transactions.count(),
            'total_balance': total,
            'income': income,
            'expense': expense,
            'transactions': serializer.data
        })

    @action(detail=False, methods=['get'])
    def customer_balance(self, request):
        """محاسبه مانده حساب یک مشتری"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'error': 'شناسه مشتری الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transactions = self.get_queryset().filter(customer__id=customer_id)
        credit = transactions.filter(
            transaction_type__in=[Transaction.Type.PAYMENT, Transaction.Type.RETURN]
        ).aggregate(total=Sum('amount'))['total'] or 0
        debt = transactions.filter(
            transaction_type=Transaction.Type.ORDER_DEBT
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'customer_id': customer_id,
            'balance': debt - credit,
            'debt': debt,
            'credit': credit,
            'transaction_count': transactions.count()
        })

    @action(detail=False, methods=['get'])
    def my_summary(self, request):
        """گزارش مالی شخصی مشتری: مانده‌ها، خرید کل، تراکنش‌های امروز/هفته/ماه"""
        user = self.request.user
        profile = getattr(user, 'customer_profile', None)
        if profile is None:
            return Response({'error': 'حساب مشتری یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        qs = Transaction.objects.filter(customer=profile)

        orders = Order.objects.filter(customer=profile)
        total_purchase = sum(
            int(o.total_price) for o in orders if o.status not in ['CANCELLED']
        )
        total_paid = sum(
            int(p.amount) for p in Payment.objects.filter(
                order__customer=profile, status=Payment.Status.SUCCESS
            )
        )

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        def _sum_range(start):
            tx = qs.filter(created_at__date__gte=start, created_at__date__lte=today)
            income = tx.filter(
                transaction_type__in=[Transaction.Type.PAYMENT, Transaction.Type.RETURN]
            ).aggregate(total=Sum('amount'))['total'] or 0
            expense = tx.filter(
                transaction_type=Transaction.Type.ORDER_DEBT
            ).aggregate(total=Sum('amount'))['total'] or 0
            return int(income), int(expense)

        daily_income, daily_expense = _sum_range(today)
        weekly_income, weekly_expense = _sum_range(week_start)
        monthly_income, monthly_expense = _sum_range(month_start)

        credit_total = qs.filter(
            transaction_type__in=[Transaction.Type.PAYMENT, Transaction.Type.RETURN]
        ).aggregate(total=Sum('amount'))['total'] or 0
        debt_total = qs.filter(
            transaction_type=Transaction.Type.ORDER_DEBT
        ).aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'customer_id': profile.id,
            'balance': int(profile.account_balance),
            'debt': int(debt_total),
            'credit': int(credit_total),
            'total_purchase': int(total_purchase),
            'total_paid': int(total_paid),
            'today': {'income': daily_income, 'expense': daily_expense},
            'week': {'income': weekly_income, 'expense': weekly_expense},
            'month': {'income': monthly_income, 'expense': monthly_expense},
            'transaction_count': qs.count(),
            'orders_count': orders.count(),
        })

    @action(detail=False, methods=['get'])
    def debtors(self, request):
        """لیست بدهکاران"""
        # مشتریانی که تراکنش منفی دارند
        debtors = self.get_queryset().filter(
            transaction_type=Transaction.Type.ORDER_DEBT
        ).values('customer__id', 'customer__company_name', 'customer__phone').annotate(
            total_debt=Sum('amount'),
            transaction_count=Count('id')
        )
        
        result = []
        for debtor in debtors:
            # بدهی خالص = برداشت‌ها - واریزهای همان مشتری
            credit = Transaction.objects.filter(
                customer__id=debtor['customer__id'],
                transaction_type__in=[Transaction.Type.PAYMENT, Transaction.Type.RETURN]
            ).aggregate(total=Sum('amount'))['total'] or 0
            net_debt = debtor['total_debt'] - credit
            if net_debt > 0:
                result.append({
                    'id': debtor['customer__id'],
                    'name': debtor['customer__company_name'] or 'بدون نام',
                    'phone': debtor['customer__phone'],
                    'total_debt': net_debt,
                    'transaction_count': debtor['transaction_count']
                })
        
        return Response(result)

    @staticmethod
    def _to_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    @classmethod
    def _date_range(cls, request):
        """محاسبه بازه زمانی بر اساس پارامتر period"""
        today = datetime.now().date()
        period = request.query_params.get('period', 'month')
        from_date = cls._to_date(request.query_params.get('from_date'))
        to_date = cls._to_date(request.query_params.get('to_date'))

        if period == 'today':
            return today, today
        if period == 'week':
            return today - timedelta(days=today.weekday()), today
        if period == 'month':
            return today.replace(day=1), today
        if period == 'year':
            return today.replace(month=1, day=1), today
        if period == 'custom':
            if not from_date and not to_date:
                return today.replace(day=1), today
            return from_date or today.replace(day=1), to_date or today
        if from_date or to_date:
            return from_date or today.replace(day=1), to_date or today
        return today.replace(day=1), today

    @staticmethod
    def _order_payment_info(order):
        """پرداخت شده، مانده و روش پرداخت یک سفارش"""
        success_payments = [
            p for p in order.payments.all() if p.status == Payment.Status.SUCCESS
        ]
        paid = sum(int(p.amount) for p in success_payments)
        total = int(order.total_price)
        remaining = max(total - paid, 0)
        method = '---'
        if order.payments.exists():
            method = order.payments.order_by('-created_at').first().method
        return paid, remaining, method

    @staticmethod
    def _order_status_label(status):
        labels = {
            'PENDING': 'در انتظار',
            'CONFIRMED': 'تایید شده',
            'PREPARING': 'در حال آماده‌سازی',
            'SHIPPED': 'ارسال شده',
            'DELIVERED': 'تحویل شده',
            'CANCELLED': 'لغو شده',
        }
        return labels.get(status, status)

    def _build_chart(self, granularity, distributor=None):
        """نمودار فروش بر اساس بازه‌های زمانی"""
        today = datetime.now().date()

        if granularity == 'weekly':
            count = 8
            starts = []
            for i in range(count - 1, -1, -1):
                d = today - timedelta(weeks=i)
                starts.append(d - timedelta(days=d.weekday()))
            window_start = (starts[0] if starts else today) - timedelta(days=1)
            bucket_key = lambda d: d - timedelta(days=d.weekday())
            key_label = lambda k: k.strftime('%Y-%m-%d')
            default = lambda k: 0
        elif granularity == 'monthly':
            count = 6
            starts = []
            year, month = today.year, today.month
            for i in range(count - 1, -1, -1):
                m_total = year * 12 + (month - 1) - i
                starts.append((m_total // 12, m_total % 12 + 1))
            window_start = datetime(starts[0][0], starts[0][1], 1).date()
            bucket_key = lambda d: (d.year, d.month)
            key_label = lambda k: f"{k[0]:04d}-{k[1]:02d}"
            default = lambda k: 0
        elif granularity == 'yearly':
            count = 5
            years = [today.year - i for i in range(count - 1, -1, -1)]
            window_start = datetime(years[0], 1, 1).date()
            bucket_key = lambda d: d.year
            key_label = lambda k: f"{k}"
            default = lambda k: 0
        else:
            granularity = 'daily'
            count = 7
            starts = [(today - timedelta(days=i)) for i in range(count - 1, -1, -1)]
            window_start = (starts[0] if starts else today) - timedelta(days=1)
            bucket_key = lambda d: d
            key_label = lambda k: k.strftime('%Y-%m-%d')
            default = lambda k: 0

        orders = Order.objects.filter(
            status__in=SALES_STATUSES,
            created_at__date__gte=window_start
        )
        if distributor is not None:
            orders = orders.filter(customer__distributor=distributor)
        orders = orders.annotate(d=TruncDate('created_at')).values('d').annotate(
            t=Sum('total_price'),
            c=Count('id')
        )

        buckets = OrderedDict()
        if granularity == 'monthly':
            for y, m in starts:
                buckets[(y, m)] = {'label': key_label((y, m)), 'total': 0, 'count': 0}
        elif granularity == 'yearly':
            for y in years:
                buckets[y] = {'label': key_label(y), 'total': 0, 'count': 0}
        else:
            for s in starts:
                buckets[s] = {'label': key_label(s), 'total': 0, 'count': 0}

        for row in orders:
            d = row['d']
            if d is None:
                continue
            key = bucket_key(d)
            if key not in buckets:
                continue
            buckets[key]['total'] += int(row['t'] or 0)
            buckets[key]['count'] += row['c']

        return list(buckets.values())

    def _build_debtors(self, distributor=None):
        customers = Customer.objects.filter(
            account_balance__gt=0, is_active=True
        ).select_related('user', 'distributor').order_by('-account_balance')
        if distributor is not None:
            customers = customers.filter(distributor=distributor)
        result = []
        for c in customers:
            name = c.company_name or c.user.get_full_name() or (c.user.username if c.user else 'بدون نام')
            open_tickets = 0
            if c.user_id:
                open_tickets = Ticket.objects.filter(
                    user_id=c.user_id, status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]
                ).count()
            result.append({
                'id': c.id,
                'name': name,
                'phone': c.phone,
                'total_debt': abs(int(c.account_balance)),
                'orders_count': c.orders.count(),
                'open_tickets': open_tickets,
            })
        return result

    def _build_settlements(self, from_date, to_date, distributor=None):
        result = []
        dist_qs = Distributor.objects.filter(is_active=True)
        if distributor is not None:
            # پخش‌کننده فقط تسویه خودش با شرکت را می‌بیند
            dist_qs = dist_qs.filter(pk=distributor.pk)
        for dist in dist_qs.prefetch_related('customers'):
            customer_ids = list(dist.customers.values_list('id', flat=True))
            orders = Order.objects.filter(
                customer_id__in=customer_ids,
                status__in=SALES_STATUSES
            )
            if from_date:
                orders = orders.filter(created_at__date__gte=from_date)
            if to_date:
                orders = orders.filter(created_at__date__lte=to_date)

            total_amount = sum(int(o.total_price) for o in orders)
            payments = Payment.objects.filter(
                order__in=orders,
                status=Payment.Status.SUCCESS
            )
            settled = sum(int(p.amount) for p in payments)
            balance = total_amount - settled
            last = payments.order_by('-created_at').first()
            result.append({
                'id': dist.id,
                'name': dist.full_name,
                'city': dist.city,
                'total_amount': total_amount,
                'settled': settled,
                'balance': balance,
                'last_settlement': last.created_at.strftime('%Y-%m-%d') if last else None,
                'status': 'settled' if balance <= 0 else 'unsettled',
            })
        return result

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """خلاصه مالی کامل: کارت‌ها، نمودار، فاکتورها، بدهکاران و تسویه پخش‌کنندگان"""
        from_date, to_date = self._date_range(request)
        granularity = request.query_params.get('granularity', 'daily')
        search_name = (request.query_params.get('customer_name') or '').strip()
        search_invoice = (request.query_params.get('invoice_number') or '').strip()

        # پخش‌کننده فقط داده‌های مشتریان خودش را می‌بیند
        dist_profile = self._distributor_profile(request.user)

        sales_orders = Order.objects.filter(status__in=SALES_STATUSES)
        if dist_profile is not None:
            sales_orders = sales_orders.filter(customer__distributor=dist_profile)
        range_orders = sales_orders
        if from_date:
            range_orders = range_orders.filter(created_at__date__gte=from_date)
        if to_date:
            range_orders = range_orders.filter(created_at__date__lte=to_date)

        total_sales = sum(int(o.total_price) for o in range_orders)

        # تخفیف اعمال‌شده روی اقلام سفارش‌های تحویل‌شده
        total_discount = 0
        discount_items = OrderItem.objects.filter(
            order__in=range_orders,
            product__discount_percent__gt=0
        ).select_related('product')
        for item in discount_items:
            base = int(item.product.base_price) if item.product.base_price else 0
            if base > int(item.price):
                total_discount += (base - int(item.price)) * item.quantity

        total_balance = int(Customer.objects.aggregate(total=Sum('account_balance'))['total'] or 0)
        if dist_profile is not None:
            total_balance = int(Customer.objects.filter(
                distributor=dist_profile
            ).aggregate(total=Sum('account_balance'))['total'] or 0)

        invoices_orders = Order.objects.filter(created_at__date__range=[from_date, to_date]).select_related(
            'customer__user', 'customer__distributor'
        ).prefetch_related('payments').order_by('-created_at')
        if dist_profile is not None:
            invoices_orders = invoices_orders.filter(customer__distributor=dist_profile)

        if search_name:
            invoices_orders = invoices_orders.filter(
                Q(customer__company_name__icontains=search_name)
                | Q(customer__user__first_name__icontains=search_name)
                | Q(customer__user__last_name__icontains=search_name)
                | Q(customer__user__username__icontains=search_name)
                | Q(customer__phone__icontains=search_name)
            )
        if search_invoice:
            invoices_orders = invoices_orders.filter(
                Q(id=search_invoice) | Q(tracking_code__icontains=search_invoice)
            )

        invoices_orders = invoices_orders[:300]

        invoices = []
        for o in invoices_orders:
            paid, remaining, method = self._order_payment_info(o)
            customer = o.customer
            receipts = []
            for p in o.payments.all().order_by('-created_at'):
                if p.receipt:
                    url = p.receipt.url
                    if request:
                        url = request.build_absolute_uri(url)
                    receipts.append({
                        'url': url,
                        'name': p.receipt.name.split('/')[-1],
                        'amount': int(p.amount),
                        'status': p.status,
                    })
            invoices.append({
                'id': o.id,
                'invoice_number': o.tracking_code or f"#{o.id}",
                'date': o.created_at.strftime('%Y-%m-%d'),
                'description': customer.company_name or customer.user.get_full_name() or f'مشتری #{customer.id}',
                'amount': int(o.total_price),
                'paid': paid,
                'remaining': remaining,
                'method': method,
                'status': o.status,
                'status_label': self._order_status_label(o.status),
                'customer_id': customer.id,
                'receipts': receipts,
            })

        return Response({
            'summary': {
                'total_sales': total_sales,
                'total_discount': total_discount,
                'total_balance': total_balance,
            },
            'chart': self._build_chart(granularity, dist_profile),
            'invoices': invoices,
            'debtors': self._build_debtors(dist_profile),
            'settlements': self._build_settlements(from_date, to_date, dist_profile),
        })


class IsAdminOrSecretaryOrOwnPendingCheck(BasePermission):
    """
    منشی/ادمین: دسترسی کامل روی همه چک‌ها.
    مشتری: فقط می‌تواند چک خودش را که هنوز در انتظار بررسی است حذف کند.
    """
    def has_permission(self, request, view):
        return request.user.role in ['ADMIN', 'SECRETARY', 'CUSTOMER']

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ['ADMIN', 'SECRETARY']:
            return True
        return (
            user.role == 'CUSTOMER'
            and obj.customer_id
            and getattr(obj.customer, 'user_id', None) == user.id
            and obj.status == Check.Status.PENDING
        )


class CheckViewSet(viewsets.ModelViewSet):
    """
    مدیریت کامل چک‌ها
    """
    
    serializer_class = CheckSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'customer__id']
    search_fields = ['check_number', 'customer__company_name', 'bank_name']
    ordering_fields = ['due_date', 'amount', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminOrSecretaryOrOwnPendingCheck()]
        if self.action in ['update', 'partial_update', 'cash_check', 'approve', 'reject']:
            return [IsAdminOrSecretary()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['ADMIN', 'SECRETARY']:
            return Check.objects.select_related('customer').all()
        
        if user.role == 'DISTRIBUTOR':
            return Check.objects.filter(
                customer__distributor__user=user
            ).select_related('customer')
        
        if user.role == 'CUSTOMER':
            return Check.objects.filter(
                customer__user=user
            ).select_related('customer')
        
        return Check.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        check = None

        if user.role == 'CUSTOMER':
            profile = getattr(user, 'customer_profile', None)
            if profile is None:
                raise exceptions.ValidationError('حساب مشتری برای شما یافت نشد')
            # مشتری فقط می‌تواند چک برای خودش ثبت کند
            check = serializer.save(customer=profile, registered_by=user.role)
        else:
            if not serializer.validated_data.get('customer'):
                raise exceptions.ValidationError('انتخاب مشتری برای ثبت چک الزامی است')
            check = serializer.save(registered_by=user.role)

        AuditService.log(
            user=self.request.user,
            action="CREATE",
            model_name="Check",
            object_id=check.id,
            description=f"Check {check.check_number} created by {self.request.user.username}"
        )

    def perform_update(self, serializer):
        check = serializer.save()
        AuditService.log(
            user=self.request.user,
            action="UPDATE",
            model_name="Check",
            object_id=check.id,
            description=f"Check {check.check_number} updated by {self.request.user.username}"
        )

    def perform_destroy(self, instance):
        check_id = instance.id
        check_number = instance.check_number
        instance.delete()
        AuditService.log(
            user=self.request.user,
            action="DELETE",
            model_name="Check",
            object_id=check_id,
            description=f"Check {check_number} deleted by {self.request.user.username}"
        )

    @action(detail=True, methods=['post'])
    def cash_check(self, request, pk=None):
        """نقد کردن چک"""
        check = self.get_object()
        
        if check.status == Check.Status.PAID:
            return Response(
                {'error': 'این چک قبلاً نقد شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if check.status == Check.Status.REJECTED:
            return Response(
                {'error': 'این چک رد شده است و قابل نقد کردن نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        check.status = Check.Status.PAID
        check.save()
        
        # نقد شدن چک یعنی دریافت پول از مشتری؛ مانده حساب و تراکنش
        # به صورت یکجا توسط سرویس مالی ثبت می‌شود
        FinanceService.add_payment(
            check.customer,
            check.amount,
            f"نقد شدن چک شماره {check.check_number}"
        )
        
        AuditService.log(
            user=request.user,
            action="CASH",
            model_name="Check",
            object_id=check.id,
            description=f"Check {check.check_number} cashed by {request.user.username}"
        )
        
        serializer = self.get_serializer(check)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """تایید چک توسط منشی/ادمین"""
        check = self.get_object()

        if check.status != Check.Status.PENDING:
            return Response(
                {'error': 'فقط چک‌های در انتظار بررسی قابل تایید هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )

        check.status = Check.Status.APPROVED
        check.save()

        AuditService.log(
            user=request.user,
            action="APPROVE",
            model_name="Check",
            object_id=check.id,
            description=f"Check {check.check_number} approved by {request.user.username}"
        )

        serializer = self.get_serializer(check)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """رد چک توسط منشی/ادمین"""
        check = self.get_object()

        if check.status != Check.Status.PENDING:
            return Response(
                {'error': 'فقط چک‌های در انتظار بررسی قابل رد هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )

        check.status = Check.Status.REJECTED
        check.save()

        AuditService.log(
            user=request.user,
            action="REJECT",
            model_name="Check",
            object_id=check.id,
            description=f"Check {check.check_number} rejected by {request.user.username}"
        )

        serializer = self.get_serializer(check)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """آمار کامل چک‌ها"""
        queryset = self.get_queryset()
        
        pending = queryset.filter(status=Check.Status.PENDING).count()
        approved = queryset.filter(status=Check.Status.APPROVED).count()
        rejected = queryset.filter(status=Check.Status.REJECTED).count()
        paid = queryset.filter(status=Check.Status.PAID).count()
        
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        pending_amount = queryset.filter(
            status__in=[Check.Status.PENDING, Check.Status.APPROVED]
        ).aggregate(total=Sum('amount'))['total'] or 0
        paid_amount = queryset.filter(status=Check.Status.PAID).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        return Response({
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'paid': paid,
            'total': pending + approved + rejected + paid,
            'total_amount': total_amount,
            'pending_amount': pending_amount,
            'paid_amount': paid_amount
        })

    @action(detail=False, methods=['get'])
    def debtors(self, request):
        """لیست بدهکاران (چک‌های نقد نشده)"""
        checks = self.get_queryset().filter(
            status__in=[Check.Status.PENDING, Check.Status.APPROVED]
        ).select_related('customer')
        
        # گروه‌بندی بر اساس مشتری
        debtors = {}
        for check in checks:
            customer = check.customer
            key = customer.id
            if key not in debtors:
                debtors[key] = {
                    'customer_id': customer.id,
                    'customer_name': customer.company_name or customer.full_name,
                    'phone': customer.phone,
                    'total_debt': 0,
                    'checks': []
                }
            debtors[key]['total_debt'] += check.amount
            debtors[key]['checks'].append({
                'id': check.id,
                'number': check.check_number,
                'amount': check.amount,
                'due_date': check.due_date,
                'status': check.status,
                'bank': check.bank_name
            })
        
        return Response(list(debtors.values()))

    @action(detail=False, methods=['get'])
    def today(self, request):
        """چک‌های امروز (دریافتی یا سررسید)"""
        today = datetime.now().date()
        
        # چک‌های دریافتی امروز
        received_today = self.get_queryset().filter(
            created_at__date=today
        )
        
        # چک‌های سررسید امروز
        due_today = self.get_queryset().filter(
            due_date=today,
            status__in=[Check.Status.PENDING, Check.Status.APPROVED]
        )
        
        received_serializer = self.get_serializer(received_today, many=True)
        due_serializer = self.get_serializer(due_today, many=True)
        
        return Response({
            'received_today': {
                'count': received_today.count(),
                'total': received_today.aggregate(total=Sum('amount'))['total'] or 0,
                'checks': received_serializer.data
            },
            'due_today': {
                'count': due_today.count(),
                'total': due_today.aggregate(total=Sum('amount'))['total'] or 0,
                'checks': due_serializer.data
            }
        })