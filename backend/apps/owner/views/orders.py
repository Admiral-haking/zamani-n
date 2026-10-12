from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.owner.permissions import IsOwner
from apps.orders.models import Order


class OwnerOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = None  # بعداً اضافه میشه
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'customer']
    search_fields = ['tracking_code']
    ordering_fields = ['created_at', 'total_price']

    def list(self, request, *args, **kwargs):
        orders = self.get_queryset()
        data = []
        for o in orders:
            data.append({
                'id': o.id,
                'customer_id': o.customer_id,
                'status': o.status,
                'total_price': o.total_price,
                'tracking_code': o.tracking_code,
                'created_at': o.created_at,
                'updated_at': o.updated_at,
            })
        return Response(data)

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'وضعیت نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        return Response({
            'id': order.id,
            'status': order.status,
            'message': f'وضعیت سفارش به {order.get_status_display()} تغییر یافت'
        })