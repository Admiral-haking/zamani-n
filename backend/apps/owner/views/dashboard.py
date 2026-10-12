from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from apps.owner.permissions import IsOwner
from apps.accounts.models import User
from apps.products.models import Product
from apps.orders.models import Order
from apps.finance.models import Transaction


class OwnerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # آمار کاربران
        total_users = User.objects.count()
        total_customers = User.objects.filter(role=User.Role.CUSTOMER).count()
        total_distributors = User.objects.filter(role=User.Role.DISTRIBUTOR).count()
        total_secretaries = User.objects.filter(role=User.Role.SECRETARY).count()
        total_admins = User.objects.filter(role=User.Role.ADMIN).count()

        # آمار محصولات
        total_products = Product.objects.filter(is_active=True).count()
        total_categories = Product.objects.values('category').distinct().count()
        featured_products = Product.objects.filter(is_featured=True, is_active=True).count()

        # آمار سفارشات
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='PENDING').count()
        today_orders = Order.objects.filter(created_at__date=today).count()
        week_orders = Order.objects.filter(created_at__gte=week_ago).count()

        # آمار مالی
        total_revenue = Transaction.objects.filter(
            transaction_type='PAYMENT'
        ).aggregate(total=Sum('amount'))['total'] or 0

        today_revenue = Transaction.objects.filter(
            transaction_type='PAYMENT',
            created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        week_revenue = Transaction.objects.filter(
            transaction_type='PAYMENT',
            created_at__gte=week_ago
        ).aggregate(total=Sum('amount'))['total'] or 0

        month_revenue = Transaction.objects.filter(
            transaction_type='PAYMENT',
            created_at__gte=month_ago
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_debt = Transaction.objects.filter(
            transaction_type='ORDER_DEBT'
        ).aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'users': {
                'total': total_users,
                'customers': total_customers,
                'distributors': total_distributors,
                'secretaries': total_secretaries,
                'admins': total_admins,
            },
            'products': {
                'total': total_products,
                'categories': total_categories,
                'featured': featured_products,
            },
            'orders': {
                'total': total_orders,
                'pending': pending_orders,
                'today': today_orders,
                'week': week_orders,
            },
            'finance': {
                'total_revenue': total_revenue,
                'today_revenue': today_revenue,
                'week_revenue': week_revenue,
                'month_revenue': month_revenue,
                'total_debt': total_debt,
            }
        }

        return Response(data)