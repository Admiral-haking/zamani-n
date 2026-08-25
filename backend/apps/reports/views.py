# backend/apps/reports/views.py
from rest_framework import viewsets
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
from apps.common.permissions.permissions import IsAdminOrSecretary


class ReportView(viewsets.ViewSet):
    """
    گزارشات پیشرفته برای پنل منشی
    """
    
    permission_classes = [IsAdminOrSecretary]

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
        
        queryset = Order.objects.filter(status='DELIVERED')
        
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
        """گزارش کامل بدهکاران"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        # بدهکاران از چک‌های نقد نشده
        checks_query = Check.objects.filter(
            status__in=[Check.Status.PENDING, Check.Status.APPROVED]
        ).select_related('customer')
        
        # بدهکاران از تراکنش‌های منفی
        transactions_query = Transaction.objects.filter(
            amount__lt=0
        ).select_related('customer')
        
        if from_date:
            checks_query = checks_query.filter(created_at__date__gte=from_date)
            transactions_query = transactions_query.filter(created_at__date__gte=from_date)
        if to_date:
            checks_query = checks_query.filter(created_at__date__lte=to_date)
            transactions_query = transactions_query.filter(created_at__date__lte=to_date)
        
        debtors_dict = {}
        
        # از چک‌ها
        for check in checks_query:
            customer = check.customer
            if customer:
                key = customer.id
                if key not in debtors_dict:
                    debtors_dict[key] = {
                        'id': customer.id,
                        'name': customer.company_name or customer.full_name,
                        'phone': customer.phone,
                        'total_debt': 0,
                        'checks': [],
                        'transactions': []
                    }
                debtors_dict[key]['total_debt'] += check.amount
                debtors_dict[key]['checks'].append({
                    'number': check.check_number,
                    'amount': check.amount,
                    'due_date': check.due_date,
                    'bank': check.bank_name,
                    'status': check.status
                })
        
        # از تراکنش‌ها
        for transaction in transactions_query:
            customer = transaction.customer
            if customer:
                key = customer.id
                if key not in debtors_dict:
                    debtors_dict[key] = {
                        'id': customer.id,
                        'name': customer.company_name or customer.full_name,
                        'phone': customer.phone,
                        'total_debt': 0,
                        'checks': [],
                        'transactions': []
                    }
                debtors_dict[key]['total_debt'] += abs(transaction.amount)
                debtors_dict[key]['transactions'].append({
                    'amount': transaction.amount,
                    'description': transaction.description,
                    'date': transaction.created_at,
                    'type': transaction.transaction_type
                })
        
        # مرتب‌سازی بر اساس میزان بدهی
        result = sorted(
            debtors_dict.values(),
            key=lambda x: x['total_debt'],
            reverse=True
        )
        
        return Response({
            'total_debtors': len(result),
            'total_debt_amount': sum(d['total_debt'] for d in result),
            'debtors': result
        })

    @action(detail=False, methods=['get'])
    def profit_loss(self, request):
        """گزارش سود و زیان"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        period = request.query_params.get('period', 'daily')  # daily, weekly, monthly, yearly
        
        queryset = Order.objects.filter(status='DELIVERED')
        
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
                status='DELIVERED'
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
        priority = request.query_params.get('priority')
        
        queryset = Ticket.objects.select_related('user')
        
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        total = queryset.count()
        open_tickets = queryset.filter(status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]).count()
        closed = queryset.filter(status=Ticket.Status.CLOSED).count()
        
        # تیکت‌های به تفکیک اولویت
        by_priority = queryset.values('priority').annotate(count=Count('id'))
        
        # تیکت‌های به تفکیک دسته‌بندی
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
                'priority': ticket.priority,
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
            'by_priority': by_priority,
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
            total_spent_annotated=Sum('orders__total_price', filter=Q(orders__status='DELIVERED'))
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
            order__status='DELIVERED'
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
            orders = Order.objects.filter(status='DELIVERED')[:100]
            for order in orders:
                writer.writerow([
                    order.id,
                    order.customer.company_name or order.customer.full_name,
                    order.total_price,
                    order.created_at.strftime('%Y-%m-%d'),
                    order.status
                ])
        
        return response