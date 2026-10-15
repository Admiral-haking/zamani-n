from django.urls import path, include

from rest_framework.routers import DefaultRouter

from apps.payments.views import PaymentViewSet, zarinpal_callback

router = DefaultRouter()

router.register(
    "",
    PaymentViewSet,
    basename="payments"
)

urlpatterns = [
    path(
        "callback/",
        zarinpal_callback,
        name="payments-callback"
    ),
    path(
        "",
        include(router.urls)
    ),
]