from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions.distributor_access import IsDistributorOrAdminSecretary
from apps.customers.models import Customer
from .models import Reminder
from .serializers import ReminderSerializer


def _distributor_profile(user):
    return getattr(user, 'distributor_profile', None)


class ReminderViewSet(viewsets.ModelViewSet):
    """یادآوری‌های پیگیری مشتری — پخش‌کننده فقط مشتریان خودش، منشی/ادمین همه"""

    serializer_class = ReminderSerializer
    permission_classes = [IsDistributorOrAdminSecretary]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = Reminder.objects.select_related('customer', 'customer__user', 'created_by')
        if not user.is_authenticated:
            return qs.none()
        if user.role in ['ADMIN', 'SECRETARY']:
            return qs.all()
        if user.role == 'DISTRIBUTOR':
            profile = _distributor_profile(user)
            if profile is None:
                return qs.none()
            return qs.filter(customer__distributor=profile)
        return qs.none()

    def _customer_in_scope(self, customer_id):
        user = self.request.user
        try:
            customer = Customer.objects.select_related('distributor').get(pk=customer_id)
        except (Customer.DoesNotExist, ValueError, TypeError):
            return None
        if user.role in ['ADMIN', 'SECRETARY']:
            return customer
        if user.role == 'DISTRIBUTOR':
            profile = _distributor_profile(user)
            if profile is not None and customer.distributor_id == profile.id:
                return customer
        return None

    def perform_create(self, serializer):
        customer_id = self.request.data.get('customer')
        customer = self._customer_in_scope(customer_id)
        if customer is None:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('مشتری معتبر برای ثبت یادآوری یافت نشد.')
        serializer.save(customer=customer, created_by=self.request.user)

    def perform_update(self, serializer):
        # تغییر مشتری از این مسیر مجاز نیست
        serializer.validated_data.pop('customer', None)
        serializer.save()

    @action(detail=True, methods=['post'])
    def done(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_done = True
        reminder.save(update_fields=['is_done', 'updated_at'])
        return Response(self.get_serializer(reminder).data)

    @action(detail=True, methods=['post'])
    def undone(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_done = False
        reminder.save(update_fields=['is_done', 'updated_at'])
        return Response(self.get_serializer(reminder).data)
