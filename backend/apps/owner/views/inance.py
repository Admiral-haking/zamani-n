from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum

from apps.owner.permissions import IsOwner
from apps.finance.models import Transaction


class OwnerFinancialReportView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        total_revenue = Transaction.objects.filter(
            transaction_type='PAYMENT'
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_debt = Transaction.objects.filter(
            transaction_type='ORDER_DEBT'
        ).aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'total_revenue': total_revenue,
            'total_debt': total_debt,
            'transactions': Transaction.objects.all().order_by('-created_at')[:50]
        })