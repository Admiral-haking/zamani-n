from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'اعلان به عنوان خوانده شده علامت‌گذاری شد'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'message': 'همه اعلانات به عنوان خوانده شده علامت‌گذاری شدند'})

    @action(detail=True, methods=['post'])
    def delete_notification(self, request, pk=None):
        notification = self.get_object()
        notification.is_deleted = True
        notification.save()
        return Response({'message': 'اعلان حذف شد'})
