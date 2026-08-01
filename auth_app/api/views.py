from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import RegistrationSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import CookieTokenObtainPairSerializer

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'User created successfully!'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CookieTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get('refresh')
        access = response.data.get('access')
        user = response.data.get('user')

        response.set_cookie(
            key='access_token',
            value=access,
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        response.set_cookie(
                    key='refresh_token',
                    value=refresh,
                    httponly=True,
                    secure=False,
                    samesite='Lax'
                )
        response.data = {'detail': 'Login successfully!', 'user': user}
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response(
                {'detail': 'Refresh token not found!'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = self.get_serializer(data={'refresh':refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {'detail': 'Refresh token invalid!'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get('access')
        response = Response({'detail': 'Token refreshed'})
        response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    secure=False,
                    samesite='Lax'
                )
        return response


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response(
                {'detail': 'Refresh token not found!'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {'detail': 'User is already logged out!'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        response = Response(
                        {'detail': 'Log-Out successfully! '
                        'All Tokens will be deleted. '
                        'Refresh token is now invalid.'},
                        status=status.HTTP_200_OK,
                    )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response