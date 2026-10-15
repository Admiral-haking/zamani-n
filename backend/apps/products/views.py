from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import Product, Category
from .serializers.product_serializer import ProductSerializer
from .serializers.category_serializer import CategorySerializer
from apps.audit.services import AuditService
from apps.common.permissions.permissions import (
    IsAdminOrSecretary
)


class ProductViewSet(viewsets.ModelViewSet):

    queryset = (
        Product.objects
        .select_related(
            "category"
        )
        .all()
    )

    serializer_class = ProductSerializer

    # همه محصولات در یک پاسخ (بدون پیجینگ) برای فیلترها و dropdown ها
    pagination_class = None

    def get_permissions(self):

        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy"
        ]:
            return [
                IsAdminOrSecretary()
            ]

        return [
            IsAuthenticated()
        ]

    def perform_create(self, serializer):
        product = serializer.save()

        AuditService.log(
            user=self.request.user,
            action="CREATE",
            model_name="Product",
            object_id=product.id,
            description=f"Created product {product.name}"
        )

    def perform_update(self, serializer):
        product = serializer.save()

        AuditService.log(
            user=self.request.user,
            action="UPDATE",
            model_name="Product",
            object_id=product.id,
            description=f"Updated product {product.name}"
        )

    def perform_destroy(self, instance):
        product_id = instance.id
        product_name = instance.name

        instance.delete()

        AuditService.log(
            user=self.request.user,
            action="DELETE",
            model_name="Product",
            object_id=product_id,
            description=f"Deleted product {product_name}"
        )


class CategoryViewSet(viewsets.ModelViewSet):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy"
        ]:
            return [
                IsAdminOrSecretary()
            ]

        return [
            IsAuthenticated()
        ]

    def perform_create(self, serializer):
        category = serializer.save()

        AuditService.log(
            user=self.request.user,
            action="CREATE",
            model_name="Category",
            object_id=category.id,
            description=f"Created category {category.name}"
        )


# ========================================
# 👇 API جدید برای پرفروش‌ترین محصولات
# ========================================
@api_view(['GET'])
@permission_classes([AllowAny])
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