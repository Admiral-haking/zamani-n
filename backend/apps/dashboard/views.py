# backend/apps/dashboard/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from datetime import datetime, timedelta

from apps.orders.models import Order
from apps.products.models import Product
from apps.customers.models import Customer
from apps.inventory.models import Inventory
from apps.tickets.models import Ticket


class DashboardView(APIView):
    """
    داشبورد کامل برای پنل منشی
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = datetime.now().date()
            
            # ===== آمار پایه =====
            total_customers = Customer.objects.filter(is_active=True).count()
            total_products = Product.objects.filter(is_active=True).count()
            total_orders = Order.objects.count()
            
            # ===== سفارشات امروز =====
            today_orders = Order.objects.filter(created_at__date=today)
            today_orders_count = today_orders.count()
            today_income = today_orders.aggregate(
                total=Sum('total_price')
            )['total'] or 0
            
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
                status='DELIVERED'
            )
            weekly_revenue = weekly_orders.aggregate(
                total=Sum('total_price')
            )['total'] or 0
            
            # ===== فروش ماهانه =====
            start_of_month = today.replace(day=1)
            monthly_orders = Order.objects.filter(
                created_at__date__gte=start_of_month,
                status='DELIVERED'
            )
            monthly_revenue = monthly_orders.aggregate(
                total=Sum('total_price')
            )['total'] or 0
            
            # ===== ۵ سفارش اخیر =====
            recent_orders = Order.objects.select_related(
                'customer__user'
            ).order_by('-created_at')[:5]
            
            recent_orders_data = []
            for order in recent_orders:
                recent_orders_data.append({
                    'id': order.id,
                    'customer': order.customer.company_name or order.customer.full_name,
                    'total_price': order.total_price,
                    'status': order.status,
                    'created_at': order.created_at.strftime('%Y-%m-%d %H:%M')
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
                    'user': ticket.user.username,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            # ===== نمودار فروش (هفت روز اخیر) =====
            sales_chart = []
            for i in range(7):
                day = today - timedelta(days=6-i)
                daily_orders = Order.objects.filter(
                    created_at__date=day,
                    status='DELIVERED'
                )
                daily_total = daily_orders.aggregate(
                    total=Sum('total_price')
                )['total'] or 0
                sales_chart.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'day_name': day.strftime('%A'),
                    'total': daily_total,
                    'count': daily_orders.count()
                })
            
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
                    'transactions_count': 0
                },
                'top_customers': [],
                'recent_orders': recent_orders_data,
                'recent_tickets': recent_tickets_data,
                'sales_chart': sales_chart
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)