from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.views import ProductViewSet, CategoryViewSet, get_best_sellers

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('best-sellers/', get_best_sellers, name='best-sellers'),
]