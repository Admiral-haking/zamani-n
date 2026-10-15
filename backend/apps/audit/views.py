from rest_framework import viewsets

from .models import AuditLog

from .serializers import AuditLogSerializer

from apps.common.permissions.permissions import IsAdminOrSecretary


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):


    serializer_class = AuditLogSerializer


    permission_classes = [

        IsAdminOrSecretary

    ]


    queryset = AuditLog.objects.all()