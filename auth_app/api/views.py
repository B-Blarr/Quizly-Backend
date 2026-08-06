from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import CookieTokenObtainPairSerializer, RegistrationSerializer
from .utils import set_auth_cookie, unauthorized

LOGOUT_MESSAGE = (
    'Log-Out successfully! All Tokens will be deleted. '
    'Refresh token is now invalid.'
)


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
        user = response.data.get('user')
        set_auth_cookie(response, 'access_token', response.data.get('access'))
        set_auth_cookie(response, 'refresh_token', response.data.get('refresh'))
        response.data = {'detail': 'Login successfully!', 'user': user}
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return unauthorized('Refresh token not found!')
        serializer = self.get_serializer(data={'refresh':refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return unauthorized('Refresh token invalid!')
        response = Response({'detail': 'Token refreshed'})
        set_auth_cookie(response, 'access_token', serializer.validated_data.get('access'))
        return response


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')      
        if refresh_token is None:
            return unauthorized('Refresh token not found!')     
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return unauthorized('User is already logged out!')          
        response = Response(
                        {'detail': LOGOUT_MESSAGE},status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response