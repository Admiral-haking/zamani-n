from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet, CustomerBackupViewSet

router = DefaultRouter()

router.register(
    "",
    CustomerViewSet,
    basename="customers"
)

router.register(
    "backup",
    CustomerBackupViewSet,
    basename="customer-backup"
)

urlpatterns = [
    path("", include(router.urls)),
]