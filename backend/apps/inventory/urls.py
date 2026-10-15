from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.views import InventoryLogViewSet, InventoryViewSet

router = DefaultRouter()

router.register(
    "logs",
    InventoryLogViewSet,
    basename="inventory-log"
)

router.register(
    "",
    InventoryViewSet,
    basename="inventory"
)

urlpatterns = [
    path("", include(router.urls)),
]