# backend/apps/finance/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Q, Count
from datetime import datetime, timedelta

from .models import Transaction, Check
from .serializers import (
    TransactionSerializer,
    CheckSerializer
)
from apps.audit.services import AuditService
from apps.common.permissions.permissions import IsAdminOrSecretary
from apps.finance.services import FinanceService


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
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['ADMIN', 'SECRETARY']:
            return Transaction.objects.select_related('customer', 'user').all()
        
        if user.role == 'DISTRIBUTOR':
            return Transaction.objects.filter(
                customer__distributor__user=user
            ).select_related('customer', 'user')
        
        if user.role == 'CUSTOMER':
            return Transaction.objects.filter(
                customer__user=user
            ).select_related('customer', 'user')
        
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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'cash_check']:
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
        check = serializer.save()
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