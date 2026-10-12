# backend/apps/finance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, CheckViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'checks', CheckViewSet, basename='check')

urlpatterns = [
    path('', include(router.urls)),
]