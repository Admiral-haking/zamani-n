from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.products.models import Product, Category
from apps.products.serializers import (
    ProductSerializer,
    CategorySerializer,
)
from apps.products.permissions import IsAdminOrSecretary


class CategoryViewSet(viewsets.ModelViewSet):

    queryset = Category.objects.all()

    serializer_class = CategorySerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrSecretary
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "name",
    ]

    ordering_fields = [
        "name",
        "created_at",
    ]

    ordering = [
        "name",
    ]


class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.select_related("category").filter(is_active=True)

    serializer_class = ProductSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrSecretary
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "category",
        "is_active",
    ]

    search_fields = [
        "name",
        "code",
    ]

    ordering_fields = [
        "name",
        "base_price",
        "weight",
    ]

    ordering = [
        "name",
    ]


# ========================================
# API پرفروش‌ترین محصولات (فقط برای کاربران لاگین‌کرده)
# ========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_best_sellers(request):
    """
    دریافت پرفروش‌ترین محصولات:
    - پیشنهاد شگفت‌انگیز: ۲ محصول ویژه (is_featured=True)
    - تخفیف‌ها: محصولات با تخفیف (discount_percent>0)
    - انتخاب همیشگی: محصولات با بیش از ۲ خرید تکراری در ۱۴ روز اخیر
    """

    two_weeks_ago = timezone.now() - timedelta(days=14)

    # 1. پیشنهاد شگفت‌انگیز (ویژه)
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    )[:2]

    # 2. تخفیف‌ها
    discounted_products = Product.objects.filter(
        discount_percent__gt=0,
        is_active=True
    )[:6]

    # 3. انتخاب همیشگی شما (بیشترین خرید تکراری در ۲ هفته اخیر)
    popular_products = Product.objects.filter(
        order_items__order__created_at__gte=two_weeks_ago,
        is_active=True
    ).annotate(
        order_count=Count('order_items')
    ).filter(
        order_count__gt=2
    ).distinct()[:2]

    # سریالایزر
    featured_serializer = ProductSerializer(featured_products, many=True)
    discounted_serializer = ProductSerializer(discounted_products, many=True)
    popular_serializer = ProductSerializer(popular_products, many=True)

    return Response({
        'featured': featured_serializer.data,
        'discounted': discounted_serializer.data,
        'popular': popular_serializer.data
    })