from rest_framework import viewsets

from apps.inventory.models import Inventory
from apps.inventory.serializers import InventorySerializer
from apps.products.permissions import IsAdminOrSecretary


class InventoryViewSet(viewsets.ModelViewSet):

    queryset = Inventory.objects.select_related("product")

    serializer_class = InventorySerializer

    permission_classes = [
        IsAdminOrSecretary
    ]