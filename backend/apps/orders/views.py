# backend/apps/orders/views.py
import json

from rest_framework import viewsets, status, exceptions
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
from apps.payments.models import Payment
from apps.finance.services import FinanceService
from apps.customers.models import Customer


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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'change_status', 'confirm', 'prepare', 'ship', 'deliver', 'mark_printed']:
            return [IsAdminOrSecretary()]
        if self.action in ['cancel', 'confirm_delivery', 'approve_balance', 'reject_balance']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        
        # منشی و ادمین: همه سفارشات
        if user.role in ['ADMIN', 'SECRETARY']:
            return Order.objects.select_related(
                'customer__user'
            ).prefetch_related(
                'items__product', 'payments'
            ).all()
        
        # توزیع‌کننده: سفارشات مشتریان خودش
        if user.role == 'DISTRIBUTOR':
            return Order.objects.filter(
                customer__distributor__user=user
            ).select_related(
                'customer__user'
            ).prefetch_related(
                'items__product', 'payments'
            )
        
        # مشتری: فقط سفارشات خودش
        if user.role == 'CUSTOMER':
            return Order.objects.filter(
                customer__user=user
            ).select_related(
                'customer__user'
            ).prefetch_related(
                'items__product', 'payments'
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
            customer = Customer.objects.filter(id=customer_id).first()
            if not customer:
                return Response(
                    {'error': 'مشتری یافت نشد'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif user.role == 'DISTRIBUTOR':
            # پخش‌کننده فقط می‌تواند برای مشتریان زیرمجموعه خودش سفارش ثبت کند.
            # قیمت هر قلم از فیلد price همان آیتم (قیمت دستی) استفاده می‌شود.
            customer_id = request.data.get('customer')
            if not customer_id:
                return Response(
                    {'error': 'شناسه مشتری الزامی است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            customer = Customer.objects.filter(
                id=customer_id,
                distributor=user.distributor_profile
            ).first()
            if not customer:
                return Response(
                    {'error': 'مشتری یافت نشد یا زیرمجموعه شما نیست'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'اجازه ایجاد سفارش را ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )

        request_items = request.data.get("items")

        if request_items is not None and not isinstance(request_items, list):

            try:
                request_items = json.loads(request_items)
            except (TypeError, ValueError):
                request_items = None

        # سفارش مشتری باید دقیقاً همان اقلام انتخاب‌شده در سبد را داشته باشد؛
        # استفاده از سبد قدیمی سرور می‌توانست سفارش اشتباهی ثبت کند.
        if user.role == 'CUSTOMER':
            customer_entries = [
                raw for raw in (request_items or [])
                if isinstance(raw, dict)
            ]
            if not customer_entries:
                return Response(
                    {'error': 'سبد خرید ارسال نشده است'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # قیمت و محصول ارسالی فقط برای فروش دستی پرسنل/پخش‌کننده معتبر است؛
        # سفارش مشتری همیشه با قیمت معتبر سمت سرور ساخته می‌شود.
        manual_sale = user.role in ['ADMIN', 'SECRETARY', 'DISTRIBUTOR']

        # روش پرداخت «مانده‌حساب» برای مشتری یک «درخواست» است: بدهی و کسر
        # موجودی تا تأیید پخش‌کننده ثبت نمی‌شود و فاکتور در انتظار او می‌ماند.
        is_balance_request = (
            user.role == 'CUSTOMER'
            and str(request.data.get("payment_method") or "").upper() == 'BALANCE'
        )

        try:
            order = OrderService.create_order_from_cart(
                customer,
                request_items=request_items,
                defer_debt=is_balance_request,
                trust_client_prices=manual_sale,
                allow_product_creation=manual_sale,
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ثبت روش پرداخت انتخاب‌شده توسط مشتری و ساخت رکورد پرداخت
        payment_method = request.data.get('payment_method')
        if payment_method is not None:
            method_map = {
                'CASH': Payment.Method.CASH,
                'CARD': Payment.Method.CARD,
                'ONLINE': Payment.Method.ONLINE,
                'BALANCE': Payment.Method.BALANCE,
                'CHECK': Payment.Method.CHECK,
                'CHEQUE': Payment.Method.CHECK,
            }
            method = method_map.get(str(payment_method).upper())
            if method is None:
                return Response(
                    {'error': 'روش پرداخت نامعتبر است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if order.total_price and order.total_price > 0:
                payment = Payment.objects.filter(
                    order=order,
                    method=method,
                    status=Payment.Status.PENDING
                ).first()
                if payment is None:
                    payment = Payment.objects.create(
                        order=order,
                        amount=order.total_price,
                        method=method
                    )
                receipt_file = (
                    request.FILES.get("receipt")
                    or request.FILES.get("file")
                )
                if receipt_file:
                    payment.receipt = receipt_file
                    payment.save(update_fields=["receipt"])

        AuditService.log(
            user=user,
            action="CREATE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} created from cart by {user.username}"
        )

        # اطلاع‌رسانی به پخش‌کننده: مشتری زیرمجموعه درخواست خرید با
        # مانده‌حساب داده و منتظر تأیید یا لغو اوست.
        if (
            is_balance_request
            and customer.distributor_id
            and customer.distributor.user_id
        ):
            try:
                from apps.notifications.models import Notification

                customer_name = (
                    customer.company_name
                    or customer.user.get_full_name()
                    or customer.user.username
                )
                Notification.objects.create(
                    user_id=customer.distributor.user_id,
                    title="درخواست خرید با مانده حساب",
                    message=(
                        f"{customer_name} درخواست خرید با مانده‌حساب به مبلغ "
                        f"{int(order.total_price)} تومان ثبت کرد "
                        f"(فاکتور {order.tracking_code or '#' + str(order.id)})؛ "
                        f"تا زمان تأیید شما خرید نهایی نمی‌شود."
                    ),
                    type=Notification.Type.MESSAGE,
                )
            except Exception:
                pass

        return Response(
            self.get_serializer(order).data,
            status=status.HTTP_201_CREATED
        )

    def perform_update(self, serializer):
        old_status = serializer.instance.status if serializer.instance else None
        new_status = serializer.validated_data.get("status", old_status)

        if old_status == 'CANCELLED' and new_status != 'CANCELLED':
            raise exceptions.ValidationError(
                'فاکتور لغو شده قابل تغییر وضعیت نیست'
            )

        # درخواست مانده‌حساب یک مسیر مالی ویژه دارد و نباید با ویرایش عمومی
        # مستقیم به «تایید شده» برسد یا اثر مالی آن دور زده شود.
        if old_status == 'AWAITING_APPROVAL':
            raise exceptions.ValidationError(
                'درخواست مانده‌حساب فقط از مسیر تأیید/لغو یا لغو سفارش بررسی می‌شود'
            )

        order = serializer.save()

        if order.status == 'CANCELLED':
            self._handle_cancel_side_effects(order)

        AuditService.log(
            user=self.request.user,
            action="UPDATE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} updated by {self.request.user.username}"
        )
        return order

    def _handle_cancel_side_effects(self, order):
        """اثرات جانبی لغو فاکتور: برگشت مالی بدهی ثبت‌شده و ابطال پرداخت‌های در انتظار"""
        OrderService.reverse_order_finance(order)
        order.payments.filter(
            status=Payment.Status.PENDING
        ).update(
            status=Payment.Status.FAILED
        )

    def perform_destroy(self, instance):
        order_id = instance.id
        self._handle_cancel_side_effects(instance)
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

        if old_status == 'CANCELLED' and new_status != 'CANCELLED':
            return Response(
                {'error': 'فاکتور لغو شده قابل تغییر وضعیت نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # تغییر مستقیم درخواست مانده‌حساب به «تایید شده» باید همان اثر مالی
        # مسیر تأیید پخش‌کننده را داشته باشد: ثبت بدهی و کسر موجودی.
        if old_status == 'AWAITING_APPROVAL' and new_status == 'CONFIRMED':
            try:
                order = OrderService.approve_balance_request(order)
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            order.status = new_status
            order.save()

        if new_status == 'CANCELLED':
            self._handle_cancel_side_effects(order)

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

        # در صورت تأیید فاکتور، پرداخت‌های در انتظار (غیر آنلاین) نیز تسویه می‌شوند؛
        # به‌جز مانده‌حساب که باید به‌صورت بدهی مشتری باقی بماند
        offline_methods = [
            Payment.Method.CASH,
            Payment.Method.CARD,
            Payment.Method.CHECK,
        ]
        for payment in order.payments.filter(
            status=Payment.Status.PENDING,
            method__in=offline_methods
        ):
            payment.status = Payment.Status.SUCCESS
            payment.save(update_fields=['status'])
            if not payment.finance_processed:
                FinanceService.add_payment(
                    order.customer,
                    payment.amount,
                    f"Payment #{payment.id}",
                    payment=payment
                )
                payment.finance_processed = True
                payment.save(update_fields=['finance_processed'])

        AuditService.log(
            user=request.user,
            action="CONFIRM",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} confirmed by {request.user.username}"
        )
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def approve_balance(self, request, pk=None):
        """تأیید پخش‌کننده روی درخواست خرید با مانده‌حساب.

        تا پیش از این تأیید هیچ بدهی‌ای در حساب مشتری ثبت نشده است؛ با تأیید،
        بدهی دقیقاً یک‌بار ثبت و فاکتور «تایید شده» می‌شود.
        """
        order = self._get_balance_request_for_approver(request)

        if order is None:
            return self._balance_request_error()

        if order.status != 'AWAITING_APPROVAL':
            return Response(
                {'error': 'این درخواست قبلاً بررسی شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = OrderService.approve_balance_request(order)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        self._notify_customer(
            order,
            title="درخواست خرید شما تأیید شد",
            message=(
                f"پخش‌کننده خرید شما با مانده‌حساب را تأیید کرد؛ مبلغ "
                f"{int(order.total_price)} تومان به مانده حساب شما اضافه شد "
                f"(فاکتور {order.tracking_code or '#' + str(order.id)})."
            ),
        )

        AuditService.log(
            user=request.user,
            action="APPROVE",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} balance request approved by {request.user.username}"
        )

        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def reject_balance(self, request, pk=None):
        """لغو پخش‌کننده روی درخواست خرید با مانده‌حساب.

        چون تا این لحظه بدهی‌ای ثبت نشده، لغو فقط فاکتور را باطل می‌کند.
        """
        order = self._get_balance_request_for_approver(request)

        if order is None:
            return self._balance_request_error()

        if order.status != 'AWAITING_APPROVAL':
            return Response(
                {'error': 'این درخواست قبلاً بررسی شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.payments.filter(
            status=Payment.Status.PENDING
        ).update(
            status=Payment.Status.FAILED
        )

        order.status = 'CANCELLED'
        order.save(update_fields=['status'])

        self._notify_customer(
            order,
            title="درخواست خرید شما لغو شد",
            message=(
                f"پخش‌کننده درخواست خرید شما با مانده‌حساب را لغو کرد"
                f"{'؛ دلیل: ' + str(request.data.get('reason')) if request.data.get('reason') else ''}"
                f" (فاکتور {order.tracking_code or '#' + str(order.id)})."
            ),
        )

        AuditService.log(
            user=request.user,
            action="REJECT",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} balance request rejected by {request.user.username}"
        )

        return Response(self.get_serializer(order).data)

    def _get_balance_request_for_approver(self, request):
        """سفارش فقط به پخش‌کننده‌ی خودِ مشتری (یا ادمین/منشی) قابل بررسی است."""
        order = self.get_object()

        if order.status != 'AWAITING_APPROVAL':
            return order

        user = request.user

        if user.role in ['ADMIN', 'SECRETARY']:
            return order

        if (
            user.role == 'DISTRIBUTOR'
            and order.customer.distributor_id
            and order.customer.distributor.user_id == user.id
        ):
            return order

        return None

    def _balance_request_error(self):
        return Response(
            {'error': 'این درخواست متعلق به مشتریان شما نیست'},
            status=status.HTTP_403_FORBIDDEN
        )

    def _notify_customer(self, order, title, message):
        try:
            from apps.notifications.models import Notification

            if not order.customer.user_id:
                return

            Notification.objects.create(
                user_id=order.customer.user_id,
                title=title,
                message=message,
                type=Notification.Type.MESSAGE,
            )
        except Exception:
            pass

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
    def confirm_delivery(self, request, pk=None):
        """تایید تحویل گرفتن سفارش توسط مشتری (فقط مالک سفارش)."""
        order = self.get_object()

        is_owner = (
            request.user.is_authenticated
            and order.customer_id
            and order.customer.user_id == request.user.id
        )
        is_staff = request.user.role in ['ADMIN', 'SECRETARY']

        if not is_staff and not is_owner:
            return Response(
                {'error': 'فقط صاحب سفارش می‌تواند تحویل را تایید کند'},
                status=status.HTTP_403_FORBIDDEN
            )

        if order.status == 'DELIVERED':
            return Response(
                {'message': 'سفارش قبلاً تحویل گرفته شده است'},
                status=status.HTTP_200_OK
            )

        if order.status not in ['SHIPPED', 'PREPARING', 'CONFIRMED', 'PENDING']:
            return Response(
                {'error': 'این سفارش در وضعیت قابل تحویل نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'DELIVERED'
        order.save()
        if not order.tracking_code:
            order.generate_tracking_code()

        AuditService.log(
            user=request.user,
            action="DELIVER",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} delivered (confirmed by customer) by {request.user.username}"
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو سفارش (پرسنل، یا مشتری صاحب سفارش در وضعیت در انتظار)"""
        order = self.get_object()

        is_owner = (
            request.user.is_authenticated
            and order.customer_id
            and order.customer.user_id == request.user.id
        )
        is_staff = request.user.role in ['ADMIN', 'SECRETARY']

        if not is_staff and not is_owner:
            return Response(
                {'error': 'فقط صاحب سفارش یا پرسنل می‌توانند سفارش را لغو کنند'},
                status=status.HTTP_403_FORBIDDEN
            )

        if is_owner and not is_staff and order.status not in ['PENDING', 'CONFIRMED']:
            return Response(
                {'error': 'مشتری فقط می‌تواند سفارش در انتظار یا تاییدشده را لغو کند'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status in ['DELIVERED', 'CANCELLED']:
            return Response(
                {'error': 'سفارشات تحویل شده یا لغو شده قابل لغو نیستند'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'CANCELLED'
        order.save()
        self._handle_cancel_side_effects(order)
        AuditService.log(
            user=self.request.user,
            action="CANCEL",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} cancelled by {self.request.user.username}"
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

    @action(detail=True, methods=['post'])
    def mark_printed(self, request, pk=None):
        """علامت‌گذاری فاکتور به‌عنوان چاپ‌شده"""
        order = self.get_object()
        order.is_printed = True
        order.save(update_fields=['is_printed'])
        AuditService.log(
            user=request.user,
            action="PRINT",
            model_name="Order",
            object_id=order.id,
            description=f"Order #{order.id} invoice printed by {request.user.username}"
        )
        return Response(self.get_serializer(order).data)

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
