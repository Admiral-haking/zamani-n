from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SmsViewSet

router = DefaultRouter()
router.register(r'', SmsViewSet, basename='sms')

urlpatterns = [
    path('', include(router.urls)),
]
