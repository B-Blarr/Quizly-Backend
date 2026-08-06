from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate and create a new user account."""

    confirmed_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirmed_password', 'email']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def validate_email(self, value):
        """Ensure the email address is not already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def validate_password(self, value):
        """Check the password against Django's password validators."""
        password_validation.validate_password(value)
        return value

    def validate_confirmed_password(self, value):
        """Ensure both password fields contain the same value."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def save(self):
        """Create the user with a hashed password and return it."""
        pw = self.validated_data['password']
        account = User(
            email=self.validated_data['email'],
            username=self.validated_data['username'],
        )
        account.set_password(pw)
        account.save()
        return account


class CookieTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add the authenticated user's data to the token response."""

    def validate(self, attrs):
        """Return the token data enriched with the user's details."""
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
        }
        return data
