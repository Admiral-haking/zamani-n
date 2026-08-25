from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.owner.permissions import IsOwner


class OwnerSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        return Response({
            'message': 'تنظیمات صاحب شرکت',
            'settings': {
                'site_name': 'Zamani Burger',
                'site_description': 'فروشگاه اینترنتی برند زمانی',
            }
        })