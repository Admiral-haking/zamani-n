from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.owner.permissions import IsOwner
from apps.inventory.models import Inventory


class OwnerInventoryView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        inventory = Inventory.objects.select_related('product').all()
        data = []
        for item in inventory:
            data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'warehouse': item.warehouse,
                'created_at': item.created_at,
                'updated_at': item.updated_at,
            })
        return Response(data)