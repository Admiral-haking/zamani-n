# backend/apps/dashboard/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta

from apps.orders.models import Order
from apps.products.models import Product
from apps.customers.models import Customer
from apps.inventory.models import Inventory
from apps.tickets.models import Ticket
from apps.finance.models import Transaction
from apps.common.permissions.permissions import IsAdminOrSecretary
from drf_spectacular.utils import extend_schema, OpenApiTypes

# فاکتورهایی که فروش محسوب می‌شوند (خریدهای واقعی مشتری)
SALES_STATUSES = ('CONFIRMED', 'PREPARING', 'SHIPPED', 'DELIVERED')


class DashboardView(APIView):
    """
    داشبورد کامل برای پنل منشی
    """

    permission_classes = [IsAdminOrSecretary]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        try:
            # Use Django's configured timezone (Asia/Tehran), not the host UTC
            # clock, so "today" matches the dates shown to staff in the UI.
            today = timezone.localdate()

            # ===== آمار پایه =====
            total_customers = Customer.objects.filter(is_active=True).count()
            total_products = Product.objects.filter(is_active=True).count()
            total_orders = Order.objects.count()

            # ===== سفارشات امروز =====
            today_orders = Order.objects.filter(created_at__date=today)
            today_orders_count = today_orders.count()
            today_income = today_orders.exclude(
                status__in=['PENDING', 'CANCELLED']
            ).aggregate(
                total=Sum('total_price')
            )['total'] or 0

            # ===== تراکنش‌های امروز =====
            today_transactions_count = Transaction.objects.filter(
                created_at__date=today
            ).count()

            # ===== مشتریان جدید امروز =====
            today_new_customers = Customer.objects.filter(created_at__date=today).count()

            # ===== تیکت‌های باز =====
            open_tickets = Ticket.objects.filter(
                status__in=['OPEN', 'ANSWERED']
            ).count()

            # ===== موجودی کم =====
            low_stock = Inventory.objects.filter(
                quantity__lte=10
            ).count()

            # ===== سفارشات در انتظار =====
            pending_orders = Order.objects.filter(status='PENDING').count()

# ===== فروش هفتگی =====
            start_of_week = today - timedelta(days=today.weekday())
            weekly_orders = Order.objects.filter(
                created_at__date__gte=start_of_week,
                status__in=SALES_STATUSES
            )
            weekly_revenue = weekly_orders.aggregate(
                total=Sum('total_price')
            )['total'] or 0

            # ===== فروش ماهانه =====
            start_of_month = today.replace(day=1)
            monthly_orders = Order.objects.filter(
                created_at__date__gte=start_of_month,
                status__in=SALES_STATUSES
            )
            monthly_revenue = monthly_orders.aggregate(
                total=Sum('total_price')
            )['total'] or 0

            # ===== ۵ سفارش اخیر =====
            recent_orders = Order.objects.select_related(
                'customer__user'
            ).prefetch_related('payments').order_by('-created_at')[:5]

            recent_orders_data = []
            for order in recent_orders:
                recent_orders_data.append({
                    'id': order.id,
                    'customer': order.customer.company_name or order.customer.full_name,
                    'total_price': order.total_price,
                    'status': order.status,
                    'created_at': order.created_at.strftime('%Y-%m-%d %H:%M')
                })

            # ===== مشتریان برتر (فروش‌های واقعی) =====
            top_customers_qs = Order.objects.filter(
                status__in=SALES_STATUSES
            ).values(
                'customer__id',
                'customer__company_name',
                'customer__user__first_name',
                'customer__user__last_name',
                'customer__user__username'
            ).annotate(
                order_count=Count('id'),
                total_spent=Sum('total_price')
            ).order_by('-total_spent')[:5]

            top_customers_data = []
            for row in top_customers_qs:
                full_name = f"{row['customer__user__first_name']} {row['customer__user__last_name']}".strip()
                top_customers_data.append({
                    'id': row['customer__id'],
                    'name': (
                        row['customer__company_name']
                        or full_name
                        or row['customer__user__username']
                        or f"مشتری #{row['customer__id']}"
                    ),
                    'order_count': row['order_count'],
                    'total_spent': row['total_spent'],
                })

            # ===== ۵ تیکت اخیر =====
            recent_tickets = Ticket.objects.select_related(
                'user'
            ).order_by('-created_at')[:5]

            recent_tickets_data = []
            for ticket in recent_tickets:
                recent_tickets_data.append({
                    'id': ticket.id,
                    'title': ticket.title,
                    'user': ticket.user.username if ticket.user else (ticket.guest_name or 'مهمان'),
                    'status': ticket.status,
                    'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M')
                })

            # ===== نمودار فروش (بر اساس بازه انتخابی) =====
            chart_period = request.query_params.get('chart_period', 'daily')
            sales_chart = self._build_sales_chart(today, chart_period)

            # ===== کل مانده حساب مشتریان =====
            total_balance = Customer.objects.aggregate(
                total=Sum('account_balance')
            )['total'] or 0

            return Response({
                'summary': {
                    'total_customers': total_customers,
                    'total_products': total_products,
                    'total_orders': total_orders,
                    'total_balance': total_balance,
                    'open_tickets': open_tickets,
                    'low_stock': low_stock,
                    'pending_orders': pending_orders,
                    'weekly_revenue': weekly_revenue,
                    'monthly_revenue': monthly_revenue
                },
                'today': {
                    'orders_count': today_orders_count,
                    'income': today_income,
                    'new_customers': today_new_customers,
                    'transactions_count': today_transactions_count
                },
                'top_customers': top_customers_data,
                'recent_orders': recent_orders_data,
                'recent_tickets': recent_tickets_data,
                'sales_chart': sales_chart
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @staticmethod
    def _build_sales_chart(today, period):
        """نمودار فروش بر اساس بازه انتخابی (روزانه/هفتگی/ماهانه/سالانه)."""
        import calendar

        if period == 'weekly':
            count = 8
            starts = []
            for i in range(count - 1, -1, -1):
                d = today - timedelta(days=i * 7)
                starts.append(d - timedelta(days=d.weekday()))
            window_start = (starts[0] if starts else today) - timedelta(days=1)
            bucket_key = lambda d: d - timedelta(days=d.weekday())
            label_key = lambda k: k.strftime('%Y-%m-%d')
        elif period == 'monthly':
            count = 6
            starts = []
            year, month = today.year, today.month
            for i in range(count - 1, -1, -1):
                m_total = year * 12 + (month - 1) - i
                starts.append((m_total // 12, m_total % 12 + 1))
            window_start = datetime(starts[0][0], starts[0][1], 1).date()
            bucket_key = lambda d: (d.year, d.month)
            label_key = lambda k: f"{k[0]:04d}-{k[1]:02d}"
        elif period == 'yearly':
            count = 5
            years = [today.year - i for i in range(count - 1, -1, -1)]
            window_start = datetime(years[0], 1, 1).date()
            bucket_key = lambda d: d.year
            label_key = lambda k: f"{k}"
        else:
            period = 'daily'
            count = 7
            starts = [today - timedelta(days=i) for i in range(count - 1, -1, -1)]
            window_start = (starts[0] if starts else today) - timedelta(days=1)
            bucket_key = lambda d: d
            label_key = lambda k: k.strftime('%Y-%m-%d')

        orders = Order.objects.filter(
            status__in=SALES_STATUSES,
            created_at__date__gte=window_start
        ).annotate(d=TruncDate('created_at')).values('d').annotate(
            t=Sum('total_price'),
            c=Count('id')
        )

        buckets = {}
        if period == 'monthly':
            for y, m in starts:
                buckets[(y, m)] = {'label': label_key((y, m)), 'total': 0, 'count': 0}
        elif period == 'yearly':
            for y in years:
                buckets[y] = {'label': label_key(y), 'total': 0, 'count': 0}
        else:
            for s in starts:
                buckets[s] = {'label': label_key(s), 'total': 0, 'count': 0}

        for row in orders:
            d = row['d']
            if d is None:
                continue
            key = bucket_key(d)
            if key not in buckets:
                continue
            buckets[key]['total'] += int(row['t'] or 0)
            buckets[key]['count'] += row['c']

        result = list(buckets.values())
        for b in result:
            b['total'] = int(b.get('total') or 0)
        return result
