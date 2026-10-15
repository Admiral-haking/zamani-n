from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ReturnRequest
from .serializers import ReturnRequestSerializer
from apps.common.permissions.permissions import IsAdminOrSecretary


class ReturnRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ReturnRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['approve', 'reject', 'destroy', 'update', 'partial_update']:
            return [IsAdminOrSecretary()]
        if self.action == 'cancel':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ReturnRequest.objects.none()

        # منشی و ادمین: همه درخواست‌های مرجوعی
        if user.role in ['ADMIN', 'SECRETARY']:
            return ReturnRequest.objects.select_related(
                'customer__user', 'order'
            ).order_by('-created_at')

        # پخش‌کننده: مرجوعی‌های مشتریان زیرمجموعه
        if user.role == 'DISTRIBUTOR':
            return ReturnRequest.objects.filter(
                customer__distributor=user.distributor_profile
            ).select_related('customer__user', 'order').order_by('-created_at')

        # مشتری: مرجوعی‌های خودش
        if user.role == 'CUSTOMER':
            return ReturnRequest.objects.filter(
                customer=self.request.user.customer_profile
            ).select_related('order').order_by('-created_at')

        return ReturnRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(
            customer=self.request.user.customer_profile
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        return_request = self.get_object()
        if return_request.status == 'PENDING':
            return_request.status = 'CANCELLED'
            return_request.save()
            return Response({'message': 'درخواست مرجوعی لغو شد'})
        return Response(
            {'error': 'این درخواست قابل لغو نیست'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """تایید مرجوعی و بازگردانی موجودی + اعتبار مشتری"""
        from apps.inventory.models import Inventory
        from apps.finance.services import FinanceService

        return_request = self.get_object()
        if return_request.status != 'PENDING':
            return Response(
                {'error': 'فقط درخواست‌های در انتظار بررسی قابل تایید هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # بازگردانی موجودی محصول
        order_item = return_request.order_item
        if order_item:
            inventory = Inventory.objects.filter(
                product=order_item.product
            ).first()
            if inventory:
                inventory.quantity += return_request.quantity
                inventory.save()

        # کسر بدهی (اعتبار) به اندازه قیمت آیتم مرجوعی
        if order_item:
            refund = order_item.price * return_request.quantity
            FinanceService.add_payment(
                return_request.customer,
                refund,
                f"مرجوعی #{return_request.id}"
            )

        return_request.status = 'APPROVED'
        return_request.save()
        return Response(
            self.get_serializer(return_request).data
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """رد درخواست مرجوعی"""
        return_request = self.get_object()
        if return_request.status != 'PENDING':
            return Response(
                {'error': 'فقط درخواست‌های در انتظار بررسی قابل رد هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return_request.status = 'REJECTED'
        return_request.save()
        return Response(
            self.get_serializer(return_request).data
        )
