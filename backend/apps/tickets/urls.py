from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TicketViewSet

router = DefaultRouter()

router.register(
    "",
    TicketViewSet,
    basename="tickets"
)

urlpatterns = [
    path('support-chats/<int:pk>/', TicketViewSet.as_view({'get': 'support_chat_detail', 'delete': 'support_chat_delete'})),
    path('support-chats/<int:pk>/read/', TicketViewSet.as_view({'post': 'support_chat_read'})),
    path('support-chats/<int:pk>/reply/', TicketViewSet.as_view({'post': 'support_chat_reply'})),
    path('support-chats/<int:pk>/close/', TicketViewSet.as_view({'post': 'support_chat_close'})),
    *router.urls,
]
