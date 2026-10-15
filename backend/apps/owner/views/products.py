from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.owner.permissions import IsOwner
from apps.products.models import Product


class OwnerProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = None  # بعداً اضافه میشه
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_featured']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'base_price', 'created_at']

    def list(self, request, *args, **kwargs):
        products = self.get_queryset()
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'name': p.name,
                'code': p.code,
                'weight': p.weight,
                'meat_percent': p.meat_percent,
                'base_price': p.base_price,
                'discounted_price': p.get_discounted_price(),
                'is_active': p.is_active,
                'is_featured': p.is_featured,
                'discount_percent': p.discount_percent,
                'image': p.image.url if p.image else None,
                'created_at': p.created_at,
                'updated_at': p.updated_at,
            })
        return Response(data)