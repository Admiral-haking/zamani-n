from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'full_name': getattr(user, 'full_name', user.username),
            'role': user.role,  # این مهمه!
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return Response(data, status=status.HTTP_200_OK)