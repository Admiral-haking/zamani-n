from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import DistributorPriceViewSet, LegacyProductPriceViewSet, CustomerPriceViewSet



router = DefaultRouter()



router.register(

    r"",

    DistributorPriceViewSet,

    basename="prices"

)



router.register(

    r"legacy",

    LegacyProductPriceViewSet,

    basename="legacy-prices"

)



router.register(
    r"customer-prices",
    CustomerPriceViewSet,
    basename="customer-prices",
)

urlpatterns = [

    path(

        "",

        include(router.urls)

    )

]

