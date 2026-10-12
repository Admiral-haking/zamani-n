from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from apps.inventory.models import Inventory, InventoryLog
from apps.inventory.serializers import (
    InventoryLogSerializer,
    InventorySerializer,
)
from apps.products.permissions import IsAdminOrSecretary


class LogPagination(PageNumberPagination):
    page_size = 500
    page_size_query_param = "page_size"


class InventoryLogViewSet(viewsets.ModelViewSet):

    queryset = InventoryLog.objects.select_related("recorded_by")

    serializer_class = InventoryLogSerializer

    permission_classes = [
        IsAdminOrSecretary
    ]

    pagination_class = LogPagination

    filterset_fields = ["category", "direction"]

    ordering_fields = ["created_at", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        period = self.request.query_params.get("period")
        from django.utils import timezone
        from datetime import timedelta

        if period == "daily":
            queryset = queryset.filter(
                created_at__date=timezone.localdate()
            )
        elif period == "weekly":
            queryset = queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            )
        elif period == "monthly":
            queryset = queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            )
        elif period == "yearly":
            queryset = queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=365)
            )
        return queryset


class InventoryViewSet(viewsets.ModelViewSet):

    queryset = Inventory.objects.select_related("product")

    serializer_class = InventorySerializer

    permission_classes = [
        IsAdminOrSecretary
    ]