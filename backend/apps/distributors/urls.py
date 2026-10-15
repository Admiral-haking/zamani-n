from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    DistributorViewSet,
    DistributorDashboardView,
    DistributorCustomerViewSet,
    DistributorPurchaseViewSet,
)


router = DefaultRouter()


# ترتیب مهم است: مسیرهای دارای پیشوند باید قبل از پیشوند خالی ثبت شوند
# تا الگوی detail با (?P<pk>) آن‌ها را ندزدهد
router.register(
    "customers",
    DistributorCustomerViewSet,
    basename="distributor-customers"
)

router.register(
    "purchases",
    DistributorPurchaseViewSet,
    basename="distributor-purchases",
)


router.register(
    "",
    DistributorViewSet,
    basename="distributors"
)


urlpatterns = [

    path(
        "dashboard/",
        DistributorDashboardView.as_view()
    ),

]


urlpatterns += router.urls
