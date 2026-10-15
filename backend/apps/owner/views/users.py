from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.owner.permissions import IsOwner
from apps.accounts.models import User
from apps.owner.serializers import OwnerUserSerializer, UserRoleSerializer


class OwnerUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = OwnerUserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'phone', 'email']
    ordering_fields = ['created_at', 'username', 'role']

    @action(detail=True, methods=['patch'])
    def role(self, request, pk=None):
        user = self.get_object()
        serializer = UserRoleSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({
            'id': user.id,
            'is_active': user.is_active,
            'message': f'User {user.username} is now {"active" if user.is_active else "inactive"}'
        })