from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.owner.permissions import IsOwner
from apps.products.models import Product


class OwnerDiscountView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        discounted_products = Product.objects.filter(
            discount_percent__gt=0,
            is_active=True
        )
        data = [{
            'id': p.id,
            'name': p.name,
            'base_price': p.base_price,
            'discount_percent': p.discount_percent,
            'discounted_price': p.get_discounted_price(),
        } for p in discounted_products]
        return Response(data)