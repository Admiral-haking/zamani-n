from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OwnerDashboardView, OwnerUserViewSet

router = DefaultRouter()
router.register('users', OwnerUserViewSet, basename='owner-users')

urlpatterns = [
    path('dashboard/', OwnerDashboardView.as_view(), name='owner-dashboard'),
    path('', include(router.urls)),
]