# backend/apps/reports/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
import json

from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category
from apps.customers.models import Customer
from apps.inventory.models import Inventory
from apps.finance.models import Transaction, Check
from apps.tickets.models import Ticket
from apps.distributors.models import Distributor
from apps.payments.models import Payment
from apps.common.permissions.permissions import IsAdminOrSecretary
from apps.common.permissions.distributor_access import IsDistributorOrAdminSecretary

# فاکتورهایی که فروش محسوب می‌شوند (خریدهای واقعی مشتری)
SALES_STATUSES = ('CONFIRMED', 'PREPARING', 'SHIPPED', 'DELIVERED')


class ReportView(viewsets.ViewSet):
    """
    گزارشات پیشرفته برای پنل منشی
    (اکشن‌های بدهکاران/پرونده شخص/فاکتورها برای پخش‌کننده هم باز است
    ولی خودکار فقط به مشتریان همان پخش‌کننده محدود می‌شود)
    """

    permission_classes = [IsAdminOrSecretary]

    def get_permissions(self):
        if self.action in ['debtors', 'person', 'invoices']:
            return [IsDistributorOrAdminSecretary()]
        return [IsAdminOrSecretary()]

    @staticmethod
    def _distributor_profile(user):
        if user.role == 'DISTRIBUTOR':
            return getattr(user, 'distributor_profile', None)
        return None

    @staticmethod
    def _to_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _payment_info(order):
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
    def _customer_name(customer):
        if customer.company_name:
            return customer.company_name
        if customer.user_id:
            return customer.user.get_full_name() or customer.user.username
        return f'مشتری #{customer.id}'

    def list(self, request):
        return Response({
            'message': 'برای دریافت گزارش از پارامترهای زیر استفاده کنید',
            'available_reports': [
                '/api/reports/sales/',
                '/api/reports/debtors/',
                '/api/reports/profit_loss/',
                '/api/reports/distributors/',
                '/api/reports/tickets/',
                '/api/reports/inventory/',
                '/api/reports/customers/',
                '/api/reports/products/',
            ]
        })

    @action(detail=False, methods=['get'])
    def sales(self, request):
        """گزارش فروش با فیلترهای مختلف"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        product_id = request.query_params.get('product_id')
        customer_id = request.query_params.get('customer_id')
        distributor_id = request.query_params.get('distributor_id')
        
        queryset = Order.objects.filter(status__in=SALES_STATUSES)
        
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        if customer_id:
            queryset = queryset.filter(customer__id=customer_id)
        if distributor_id:
            queryset = queryset.filter(customer__distributor__id=distributor_id)
        if product_id:
            queryset = queryset.filter(items__product__id=product_id).distinct()
        
        total_sales = queryset.aggregate(total=Sum('total_price'))['total'] or 0
        total_orders = queryset.count()
        total_items = OrderItem.objects.filter(
            order__in=queryset
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # فروش به تفکیک روز
        daily_sales = queryset.extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(
            total=Sum('total_price'),
            count=Count('id')
        ).order_by('date')
        
        # فروش به تفکیک محصول
        product_sales = OrderItem.objects.filter(
            order__in=queryset
        ).values('product__name', 'product__id').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        ).order_by('-total_revenue')
        
        # جزئیات سفارشات
        orders_data = []
        for order in queryset.select_related('customer').prefetch_related('items__product')[:100]:
            orders_data.append({
                'id': order.id,
                'customer': {
                    'id': order.customer.id,
                    'name': order.customer.company_name or order.customer.full_name,
                    'phone': order.customer.phone
                },
                'total_price': order.total_price,
                'created_at': order.created_at,
                'tracking_code': order.tracking_code,
                'status': order.status,
                'items_count': order.items.count()
            })
        
        return Response({
            'summary': {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'total_items': total_items,
                'average_order_value': total_sales / total_orders if total_orders > 0 else 0
            },
            'daily_sales': daily_sales,
            'product_sales': product_sales,
            'orders': orders_data
        })

    @action(detail=False, methods=['get'])
    def debtors(self, request):
        """گزارش کامل بدهکاران (بر اساس مانده واقعی حساب از دیتابیس)"""
        from_date = self._to_date(request.query_params.get('from_date'))
        to_date = self._to_date(request.query_params.get('to_date'))
        search = (request.query_params.get('search') or '').strip()

        customers = Customer.objects.filter(
            account_balance__gt=0, is_active=True
        ).select_related('user', 'distributor').order_by('-account_balance')

        if request.user.role == 'DISTRIBUTOR':
            profile = self._distributor_profile(request.user)
            if profile is None:
                return Response({'total_debtors': 0, 'total_debt_amount': 0, 'debtors': []})
            customers = customers.filter(distributor=profile)

        if search:
            customers = customers.filter(
                Q(company_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__username__icontains=search)
            )

        debtors = []
        for customer in customers:
            name = self._customer_name(customer)

            # چک‌های نقد نشده
            checks_qs = Check.objects.filter(
                customer=customer,
                status__in=[Check.Status.PENDING, Check.Status.APPROVED]
            )
            checks = [{
                'number': ch.check_number,
                'amount': int(ch.amount),
                'due_date': ch.due_date.strftime('%Y-%m-%d') if ch.due_date else None,
                'bank': ch.bank_name,
                'status': ch.status,
            } for ch in checks_qs]
            total_checks = sum(int(ch.amount) for ch in checks_qs)

            # فاکتورهای معوق (سفارش‌های دارای مانده)
            orders_qs = customer.orders.exclude(status='CANCELLED').prefetch_related('payments')
            if from_date:
                orders_qs = orders_qs.filter(created_at__date__gte=from_date)
            if to_date:
                orders_qs = orders_qs.filter(created_at__date__lte=to_date)

            invoices = []
            for order in orders_qs:
                paid, remaining, method = self._payment_info(order)
                if remaining <= 0:
                    continue
                invoices.append({
                    'id': order.id,
                    'invoice_number': order.tracking_code or f'#{order.id}',
                    'date': order.created_at.strftime('%Y-%m-%d'),
                    'amount': int(order.total_price),
                    'paid': paid,
                    'remaining': remaining,
                    'method': method,
                    'status': order.status,
                })

            open_tickets = 0
            if customer.user_id:
                open_tickets = Ticket.objects.filter(
                    user_id=customer.user_id,
                    status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]
                ).count()

            debtors.append({
                'id': customer.id,
                'name': name,
                'phone': customer.phone,
                'national_id': customer.national_id,
                'total_debt': abs(int(customer.account_balance)),
                'total_checks': total_checks,
                'checks': checks,
                'orders_count': customer.orders.count(),
                'open_tickets': open_tickets,
                'invoices': invoices,
            })

        return Response({
            'total_debtors': len(debtors),
            'total_debt_amount': sum(d['total_debt'] for d in debtors),
            'debtors': debtors,
        })

    @action(detail=False, methods=['get'])
    def person(self, request):
        """پرونده کامل یک شخص (اطلاعات، خریدها، اقلام، فاکتورها و چک‌ها)"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'error': 'شناسه مشتری الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            customer_id = int(customer_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'شناسه مشتری نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )

        customer = Customer.objects.filter(
            id=customer_id
        ).select_related('user', 'distributor').first()
        if not customer:
            return Response(
                {'error': 'مشتری یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.user.role == 'DISTRIBUTOR':
            profile = self._distributor_profile(request.user)
            if profile is None or customer.distributor_id != profile.id:
                return Response(
                    {'error': 'مشتری یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )

        from_date = self._to_date(request.query_params.get('from_date'))
        to_date = self._to_date(request.query_params.get('to_date'))

        orders_qs = customer.orders.select_related(
            'customer__user', 'customer__distributor'
        ).prefetch_related('items__product', 'payments')
        if from_date:
            orders_qs = orders_qs.filter(created_at__date__gte=from_date)
        if to_date:
            orders_qs = orders_qs.filter(created_at__date__lte=to_date)

        purchases = []
        items = []
        invoices = []
        for order in orders_qs:
            invoice_number = order.tracking_code or f'#{order.id}'
            date_str = order.created_at.strftime('%Y-%m-%d')
            paid, remaining, method = self._payment_info(order)

            purchases.append({
                'id': order.id,
                'invoice_number': invoice_number,
                'date': date_str,
                'items_count': order.items.count(),
                'total_price': int(order.total_price),
                'status': order.status,
            })

            for item in order.items.all():
                items.append({
                    'order_id': order.id,
                    'invoice_number': invoice_number,
                    'date': date_str,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': int(item.price),
                    'total': int(item.price) * item.quantity,
                })

            if order.status != 'CANCELLED':
                invoices.append({
                    'id': order.id,
                    'invoice_number': invoice_number,
                    'date': date_str,
                    'products': [
                        {'name': item.product.name, 'quantity': item.quantity}
                        for item in order.items.all()
                    ],
                    'amount': int(order.total_price),
                    'paid': paid,
                    'remaining': remaining,
                    'method': method,
                    'status': order.status,
                    'is_printed': bool(order.is_printed),
                })

        checks = [{
            'id': ch.id,
            'check_number': ch.check_number,
            'bank_name': ch.bank_name,
            'amount': int(ch.amount),
            'issue_date': ch.issue_date.strftime('%Y-%m-%d') if ch.issue_date else None,
            'due_date': ch.due_date.strftime('%Y-%m-%d') if ch.due_date else None,
            'status': ch.status,
        } for ch in customer.checks.all()]

        info = {
            'id': customer.id,
            'name': self._customer_name(customer),
            'phone': customer.phone,
            'email': customer.user.email if customer.user_id else '',
            'national_id': customer.national_id,
            'shop_name': customer.shop_name or '',
            'company_name': customer.company_name or '',
            'address': customer.address,
            'city': customer.city,
            'postal_code': customer.postal_code,
            'distributor_name': customer.distributor.full_name if customer.distributor_id else '',
            'account_balance': int(customer.account_balance),
            'total_orders': customer.total_orders,
            'total_spent': int(customer.total_spent),
            'points': customer.points,
            'customer_code': customer.customer_code,
            'created_at': customer.created_at.strftime('%Y-%m-%d') if customer.created_at else None,
        }

        return Response({
            'info': info,
            'purchases': purchases,
            'items': items,
            'invoices': invoices,
            'checks': checks,
        })

    @action(detail=False, methods=['get'])
    def invoices(self, request):
        """گزارش عمومی فاکتورها با فیلترهای پیشرفته"""
        from_date = self._to_date(request.query_params.get('from_date'))
        to_date = self._to_date(request.query_params.get('to_date'))
        product_id = request.query_params.get('product_id')
        invoice_number = request.query_params.get('invoice_number')
        sale_type = request.query_params.get('sale_type')
        search = (request.query_params.get('search') or '').strip()

        orders = Order.objects.select_related(
            'customer__user', 'customer__distributor'
        ).prefetch_related('items__product', 'payments').order_by('-created_at')

        if request.user.role == 'DISTRIBUTOR':
            profile = self._distributor_profile(request.user)
            if profile is None:
                return Response([])
            orders = orders.filter(customer__distributor=profile)

        if from_date:
            orders = orders.filter(created_at__date__gte=from_date)
        if to_date:
            orders = orders.filter(created_at__date__lte=to_date)
        if invoice_number:
            orders = orders.filter(
                Q(id=invoice_number) | Q(tracking_code__icontains=invoice_number)
            )
        if search:
            orders = orders.filter(
                Q(customer__company_name__icontains=search)
                | Q(customer__user__first_name__icontains=search)
                | Q(customer__user__last_name__icontains=search)
                | Q(customer__phone__icontains=search)
                | Q(tracking_code__icontains=search)
            )
        if product_id:
            orders = orders.filter(items__product__id=product_id).distinct()
        if sale_type == 'distributor':
            orders = orders.filter(customer__distributor__isnull=False)

        rows = []
        for order in orders[:500]:
            paid, remaining, method = self._payment_info(order)
            customer = order.customer
            rows.append({
                'id': order.id,
                'invoice_number': order.tracking_code or f'#{order.id}',
                'date': order.created_at.strftime('%Y-%m-%d'),
                'customer_id': customer.id,
                'customer_name': self._customer_name(customer),
                'distributor_name': customer.distributor.full_name if customer.distributor_id else '',
                'products': [{'name': i.product.name, 'quantity': i.quantity} for i in order.items.all()],
                'amount': int(order.total_price),
                'paid': paid,
                'remaining': remaining,
                'method': method,
                'status': order.status,
                'is_printed': bool(order.is_printed),
            })

        return Response(rows)

    @action(detail=False, methods=['get'])
    def profit_loss(self, request):
        """گزارش سود و زیان"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        period = request.query_params.get('period', 'daily')  # daily, weekly, monthly, yearly
        
        queryset = Order.objects.filter(status__in=SALES_STATUSES)
        
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        
        total_revenue = queryset.aggregate(total=Sum('total_price'))['total'] or 0
        
        # محاسبه هزینه‌ها (فرض می‌کنیم هزینه 60% قیمت فروش است)
        total_cost = 0
        for order in queryset.prefetch_related('items__product'):
            for item in order.items.all():
                total_cost += item.price * item.quantity * 0.6
        
        profit = total_revenue - total_cost
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # سود به تفکیک دوره
        if period == 'daily':
            profit_by_period = queryset.extra(
                select={'period': 'date(created_at)'}
            ).values('period').annotate(
                revenue=Sum('total_price')
            ).order_by('period')
        elif period == 'weekly':
            profit_by_period = queryset.extra(
                select={'period': "strftime('%Y-%W', created_at)"}
            ).values('period').annotate(
                revenue=Sum('total_price')
            ).order_by('period')
        elif period == 'monthly':
            profit_by_period = queryset.extra(
                select={'period': "strftime('%Y-%m', created_at)"}
            ).values('period').annotate(
                revenue=Sum('total_price')
            ).order_by('period')
        else:  # yearly
            profit_by_period = queryset.extra(
                select={'period': "strftime('%Y', created_at)"}
            ).values('period').annotate(
                revenue=Sum('total_price')
            ).order_by('period')
        
        return Response({
            'summary': {
                'total_revenue': total_revenue,
                'total_cost': total_cost,
                'profit': profit,
                'profit_margin': profit_margin,
                'total_orders': queryset.count()
            },
            'profit_by_period': profit_by_period
        })

    @action(detail=False, methods=['get'])
    def distributors(self, request):
        """گزارش عملکرد توزیع‌کنندگان"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        distributors = Distributor.objects.filter(is_active=True)
        
        result = []
        for distributor in distributors:
            # سفارشات مشتریان این توزیع‌کننده
            orders = Order.objects.filter(
                customer__distributor=distributor,
                status__in=SALES_STATUSES
            )
            
            if from_date:
                orders = orders.filter(created_at__date__gte=from_date)
            if to_date:
                orders = orders.filter(created_at__date__lte=to_date)
            
            total_orders = orders.count()
            total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
            total_customers = Customer.objects.filter(
                distributor=distributor,
                is_active=True
            ).count()
            
            # محاسبه کمیسیون (فرض می‌کنیم کمیسیون = 5% فروش)
            commission = total_revenue * 0.05
            
            result.append({
                'id': distributor.id,
                'name': distributor.full_name,
                'city': distributor.city,
                'phone': distributor.phone,
                'total_customers': total_customers,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'commission': commission,
                'is_active': distributor.is_active,
                'created_at': distributor.created_at
            })
        
        return Response(result)

    @action(detail=False, methods=['get'])
    def tickets(self, request):
        """گزارش تیکت‌ها"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        status = request.query_params.get('status')
        
        queryset = Ticket.objects.select_related('user')
        
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        if status:
            queryset = queryset.filter(status=status)
        
        total = queryset.count()
        open_tickets = queryset.filter(status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]).count()
        closed = queryset.filter(status=Ticket.Status.CLOSED).count()
        
        # تیکت‌ها به تفکیک دسته‌بندی
        by_category = queryset.values('category').annotate(count=Count('id'))
        
        # جزئیات تیکت‌ها
        tickets_data = []
        for ticket in queryset[:50]:
            tickets_data.append({
                'id': ticket.id,
                'title': ticket.title,
                'user': {
                    'id': ticket.user.id,
                    'username': ticket.user.username,
                    'role': ticket.user.role
                },
                'status': ticket.status,
                'category': ticket.category,
                'created_at': ticket.created_at,
                'has_reply': bool(ticket.admin_reply)
            })
        
        return Response({
            'summary': {
                'total': total,
                'open': open_tickets,
                'closed': closed
            },
            'by_category': by_category,
            'tickets': tickets_data
        })

    @action(detail=False, methods=['get'])
    def inventory(self, request):
        """گزارش موجودی انبار"""
        category_id = request.query_params.get('category_id')
        low_stock_only = request.query_params.get('low_stock_only', 'false').lower() == 'true'
        
        queryset = Inventory.objects.select_related('product__category')
        
        if category_id:
            queryset = queryset.filter(product__category__id=category_id)
        if low_stock_only:
            queryset = queryset.filter(quantity__lte=F('minimum_stock'))
        
        total_products = queryset.count()
        total_items = queryset.aggregate(total=Sum('quantity'))['total'] or 0
        low_stock_count = queryset.filter(quantity__lte=F('minimum_stock')).count()
        out_of_stock = queryset.filter(quantity=0).count()
        
        # جزئیات
        inventory_data = []
        for inv in queryset:
            inventory_data.append({
                'product_id': inv.product.id,
                'product_name': inv.product.name,
                'category': inv.product.category.name if inv.product.category else 'بدون دسته',
                'quantity': inv.quantity,
                'minimum_stock': inv.minimum_stock,
                'is_low_stock': inv.quantity <= inv.minimum_stock,
                'is_out_of_stock': inv.quantity == 0,
                'last_updated': inv.updated_at
            })
        
        return Response({
            'summary': {
                'total_products': total_products,
                'total_items': total_items,
                'low_stock': low_stock_count,
                'out_of_stock': out_of_stock
            },
            'inventory': inventory_data
        })

    @action(detail=False, methods=['get'])
    def customers(self, request):
        """گزارش مشتریان"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        queryset = Customer.objects.filter(is_active=True)
        
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        
        total_customers = queryset.count()
        new_customers_today = Customer.objects.filter(created_at__date=datetime.now().date()).count()
        
        # مشتریان برتر
        top_customers = queryset.annotate(
            order_count=Count('orders'),
            total_spent_annotated=Sum('orders__total_price', filter=Q(orders__status__in=SALES_STATUSES))
        ).filter(order_count__gt=0).order_by('-total_spent_annotated')[:10]
        
        top_customers_data = []
        for customer in top_customers:
            top_customers_data.append({
                'id': customer.id,
                'name': customer.company_name or customer.full_name,
                'phone': customer.phone,
                'order_count': customer.order_count,
                'total_spent': customer.total_spent_annotated or 0,
                'points': customer.points
            })
        
        return Response({
            'total_customers': total_customers,
            'new_customers_today': new_customers_today,
            'top_customers': top_customers_data
        })

    @action(detail=False, methods=['get'])
    def products(self, request):
        """گزارش محصولات پرفروش"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        limit = int(request.query_params.get('limit', 20))
        
        order_items = OrderItem.objects.filter(
            order__status__in=SALES_STATUSES
        )
        
        if from_date:
            order_items = order_items.filter(order__created_at__date__gte=from_date)
        if to_date:
            order_items = order_items.filter(order__created_at__date__lte=to_date)
        
        top_products = order_items.values(
            'product__id',
            'product__name',
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        ).order_by('-total_revenue')[:limit]
        
        return Response(top_products)

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """خروجی Excel از گزارشات"""
        report_type = request.query_params.get('type', 'sales')
        
        # این یک نمونه ساده است - در واقع باید از کتابخانه‌های xlsx استفاده کنید
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d")}.csv"'}
        )
        
        writer = csv.writer(response)
        
        if report_type == 'sales':
            writer.writerow(['شماره سفارش', 'مشتری', 'مبلغ', 'تاریخ', 'وضعیت'])
            orders = Order.objects.filter(status__in=SALES_STATUSES)[:100]
            for order in orders:
                writer.writerow([
                    order.id,
                    order.customer.company_name or order.customer.full_name,
                    order.total_price,
                    order.created_at.strftime('%Y-%m-%d'),
                    order.status
                ])
        
        return response