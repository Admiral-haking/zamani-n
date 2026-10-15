from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomerPriceViewSet, DistributorPriceViewSet, LegacyProductPriceViewSet


router = DefaultRouter()

# Prefix routes must be registered before the empty-prefix route.
router.register("customer-prices", CustomerPriceViewSet, basename="customer-prices")
router.register("legacy", LegacyProductPriceViewSet, basename="legacy-prices")
router.register("", DistributorPriceViewSet, basename="prices")

urlpatterns = [path("", include(router.urls))]
