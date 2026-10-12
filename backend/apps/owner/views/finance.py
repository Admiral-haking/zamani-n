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

        transactions = Transaction.objects.all().order_by('-created_at')[:50]
        transactions_data = []
        for t in transactions:
            transactions_data.append({
                'id': t.id,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'description': t.description,
                'created_at': t.created_at,
                'customer': t.customer_id,
                'user': t.user_id,
            })

        return Response({
            'total_revenue': total_revenue,
            'total_debt': total_debt,
            'transactions': transactions_data,
        })