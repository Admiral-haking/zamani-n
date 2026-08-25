from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OwnerDashboardView,
    OwnerUserViewSet,
    AccountRequestListView,
    AccountRequestApproveView,
)

router = DefaultRouter()
router.register('users', OwnerUserViewSet, basename='owner-users')

urlpatterns = [
    path('dashboard/', OwnerDashboardView.as_view(), name='owner-dashboard'),
    path('account-requests/', AccountRequestListView.as_view(), name='owner-account-requests'),
    path(
        'account-requests/<int:pk>/approve/',
        AccountRequestApproveView.as_view(),
        name='owner-account-request-approve',
    ),
    path('', include(router.urls)),
]
