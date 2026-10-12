from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReportView

router = DefaultRouter()
router.register(r"", ReportView, basename="reports")

urlpatterns = [
    path("", include(router.urls)),
]
