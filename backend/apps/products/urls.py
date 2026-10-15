from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.views import ProductViewSet, CategoryViewSet, ProductDiscountViewSet, get_best_sellers

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')
router.register('discounts', ProductDiscountViewSet, basename='discount')

urlpatterns = [
    path('', include(router.urls)),
    path('best-sellers/', get_best_sellers, name='best-sellers'),
]