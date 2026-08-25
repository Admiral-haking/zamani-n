# backend/apps/orders/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .services import OrderService
from apps.audit.services import AuditService
from apps.common.permissions.permissions import IsAdminOrSecretary


class OrderViewSet(viewsets.ModelViewSet):
    """
    مدیریت کامل سفارشات برای پنل منشی
    """
    
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'customer__id']
    search_fields = ['tracking_code', 'customer__user__username', 'customer__company_name', 'customer__phone']
    ordering_fields = ['created_at', 'total_price', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'change_status', 'confirm', 'prepare', 'ship', 'deliver', 'cancel']:
            return [IsAdminOrSecretary()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        
        # منشی و ادمین: همه سفارشات
        if user.role in ['ADMIN', 'SECRETARY']:
            return Order.objects.select_related(
                'customer__user'
            ).prefetch_related(
                'items__product'
            ).all()
        
        # توزیع‌کننده: سفارشات مشتریان خودش
        if user.role == 'DISTRIBUTOR':
            return Order.objects.filter(
                customer__distributor__user=user
            ).select_related(
                'customer__user'
            ).prefetch_related(
                'items__product'
            )
        
        # مشتری: فقط سفارشات خودش
        if user.role == 'CUSTOMER':
            return Order.objects.filter(
                customer__user=user
            ).select_related(
                'customer__user'
            ).prefetch_related(
                'items__product'
            )
        
        return Order.objects.none()

    def perform_create(self, serializer):
        order = serializer.save()
        order.generate_tracking_code()
        AuditService.log(
            user=self.request.user,
            action="CREATE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} created by {self.request.user.username}"
        )

    @action(detail=False, methods=['post'])
    def create_from_cart(self, request):
        """تبدیل سبد خرید به سفارش (قیمت‌گذاری، کسر موجودی و ثبت بدهی خودکار)"""
        user = request.user

        if user.role == 'CUSTOMER':
            customer = user.customer_profile
        elif user.role in ['ADMIN', 'SECRETARY']:
            customer_id = request.data.get('customer')
            if not customer_id:
                return Response(
                    {'error': 'شناسه مشتری الزامی است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            from apps.customers.models import Customer
            customer = Customer.objects.filter(id=customer_id).first()
            if not customer:
                return Response(
                    {'error': 'مشتری یافت نشد'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'اجازه ایجاد سفارش را ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            order = OrderService.create_order_from_cart(customer)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        AuditService.log(
            user=user,
            action="CREATE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} created from cart by {user.username}"
        )
        return Response(
            self.get_serializer(order).data,
            status=status.HTTP_201_CREATED
        )

    def perform_update(self, serializer):
        order = serializer.save()
        AuditService.log(
            user=self.request.user,
            action="UPDATE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} updated by {self.request.user.username}"
        )

    def perform_destroy(self, instance):
        order_id = instance.id
        instance.delete()
        AuditService.log(
            user=self.request.user,
            action="DELETE",
            model_name="Order",
            object_id=order_id,
            description=f"Order #{order_id} deleted by {self.request.user.username}"
        )

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """تغییر وضعیت سفارش (عمومی)"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'وضعیت جدید الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'وضعیت نامعتبر. موارد مجاز: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = order.status
        order.status = new_status
        order.save()
        
        # اگر وضعیت به DELIVERED تغییر کرد، کد رهگیری تولید کن
        if new_status == 'DELIVERED' and not order.tracking_code:
            order.generate_tracking_code()
        
        AuditService.log(
            user=request.user,
            action="UPDATE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} status changed from {old_status} to {new_status}"
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """تایید سفارش"""
        order = self.get_object()
        if order.status != 'PENDING':
            return Response(
                {'error': 'فقط سفارشات در انتظار قابل تایید هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'CONFIRMED'
        order.save()
        AuditService.log(
            user=request.user,
            action="CONFIRM",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} confirmed by {request.user.username}"
        )
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def prepare(self, request, pk=None):
        """آماده‌سازی سفارش"""
        order = self.get_object()
        if order.status != 'CONFIRMED':
            return Response(
                {'error': 'فقط سفارشات تایید شده قابل آماده‌سازی هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'PREPARING'
        order.save()
        AuditService.log(
            user=request.user,
            action="PREPARE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} is being prepared by {request.user.username}"
        )
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """ارسال سفارش"""
        order = self.get_object()
        if order.status != 'PREPARING':
            return Response(
                {'error': 'فقط سفارشات آماده شده قابل ارسال هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'SHIPPED'
        order.save()
        if not order.tracking_code:
            order.generate_tracking_code()
        AuditService.log(
            user=request.user,
            action="SHIP",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} shipped by {request.user.username}"
        )
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """تحویل سفارش"""
        order = self.get_object()
        if order.status != 'SHIPPED':
            return Response(
                {'error': 'فقط سفارشات ارسال شده قابل تحویل هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'DELIVERED'
        order.save()
        AuditService.log(
            user=request.user,
            action="DELIVER",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} delivered by {request.user.username}"
        )
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو سفارش"""
        order = self.get_object()
        if order.status in ['DELIVERED', 'CANCELLED']:
            return Response(
                {'error': 'سفارشات تحویل شده یا لغو شده قابل لغو نیستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'CANCELLED'
        order.save()
        AuditService.log(
            user=request.user,
            action="CANCEL",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} cancelled by {request.user.username}"
        )
        return Response(self.get_serializer(order).data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """دریافت سفارشات امروز"""
        today = datetime.now().date()
        orders = self.get_queryset().filter(created_at__date=today)
        total_income = orders.aggregate(total=Sum('total_price'))['total'] or 0
        serializer = self.get_serializer(orders, many=True)
        return Response({
            'count': orders.count(),
            'total_income': total_income,
            'orders': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """آمار کامل سفارشات"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        pending = queryset.filter(status='PENDING').count()
        confirmed = queryset.filter(status='CONFIRMED').count()
        preparing = queryset.filter(status='PREPARING').count()
        shipped = queryset.filter(status='SHIPPED').count()
        delivered = queryset.filter(status='DELIVERED').count()
        cancelled = queryset.filter(status='CANCELLED').count()
        
        total_revenue = queryset.filter(status='DELIVERED').aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # محاسبه میانگین قیمت سفارشات
        avg_price = queryset.aggregate(
            avg=Sum('total_price') / Count('id')
        )['avg'] or 0
        
        return Response({
            'total': total,
            'pending': pending,
            'confirmed': confirmed,
            'preparing': preparing,
            'shipped': shipped,
            'delivered': delivered,
            'cancelled': cancelled,
            'total_revenue': total_revenue,
            'average_price': avg_price
        })

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """دریافت آیتم‌های یک سفارش"""
        order = self.get_object()
        items = order.items.select_related('product').all()
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_count(self, request):
        """تعداد سفارشات در انتظار"""
        count = self.get_queryset().filter(status='PENDING').count()
        return Response({'pending_orders': count})

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """سفارشات در بازه زمانی"""
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        queryset = self.get_queryset()
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'orders': serializer.data
        })

    @action(detail=False, methods=['get'])
    def top_customers(self, request):
        """مشتریان برتر بر اساس تعداد و مبلغ سفارشات"""
        queryset = self.get_queryset().filter(status='DELIVERED')
        
        top_customers = queryset.values(
            'customer__id',
            'customer__company_name',
            'customer__user__username'
        ).annotate(
            order_count=Count('id'),
            total_spent=Sum('total_price')
        ).order_by('-total_spent')[:10]
        
        return Response(top_customers)