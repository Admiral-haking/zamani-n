from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.owner.permissions import IsOwner
from apps.tickets.models import Ticket


class OwnerTicketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Ticket.objects.all().order_by('-created_at')
    serializer_class = None  # بعداً سریالایزر اضافه میشه

    def list(self, request, *args, **kwargs):
        tickets = self.get_queryset()
        data = []
        for ticket in tickets:
            data.append({
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'status': ticket.status,
                'created_at': ticket.created_at,
                'updated_at': ticket.updated_at,
            })
        return Response(data)   