from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    DistributorViewSet,
    DistributorDashboardView,
    DistributorCustomerViewSet
)


router = DefaultRouter()


router.register(
    "",
    DistributorViewSet,
    basename="distributors"
)


router.register(
    "customers",
    DistributorCustomerViewSet,
    basename="distributor-customers"
)



urlpatterns = [

    path(
        "dashboard/",
        DistributorDashboardView.as_view()
    ),

]


urlpatterns += router.urls