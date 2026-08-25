from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)

from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
)


@extend_schema(
    tags=["Accounts"],
)
class RegisterView(generics.CreateAPIView):

    serializer_class = RegisterSerializer

    permission_classes = [
        permissions.AllowAny
    ]


@extend_schema(
    tags=["Accounts"],
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful. Returns JWT tokens and user information."
        )
    },
)
class LoginView(APIView):

    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({

            "refresh": str(refresh),

            "access": str(refresh.access_token),

            "user": UserSerializer(user).data

        })


@extend_schema(
    tags=["Accounts"],
    responses=UserSerializer,
)
class MeView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        serializer = UserSerializer(
            request.user
        )

        return Response(serializer.data)