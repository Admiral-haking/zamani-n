from rest_framework.routers import DefaultRouter
from .views import ReturnRequestViewSet

router = DefaultRouter()
router.register(r'', ReturnRequestViewSet, basename='returns')

urlpatterns = router.urls