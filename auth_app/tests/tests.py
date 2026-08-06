from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    """Tests for POST /api/register/."""

    def setUp(self):
        """Create a user whose email is already taken."""
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!',
            email='test@test.de')

    def test_registration(self):
        """A valid payload creates the user and returns 201."""
        url = reverse('register')
        data = {
            'username': 'newuser', 'email': 'new@test.de',
            'password': 'SuperSecret123!',
            'confirmed_password': 'SuperSecret123!',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['detail'], 'User created successfully!')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch_returns_400(self):
        """Differing passwords are rejected on the confirmation field."""
        url = reverse('register')
        data = {
            'username': 'newuser', 'email': 'new@test.de',
            'password': 'SuperSecret123!',
            'confirmed_password': 'differentpassword',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn('confirmed_password', response.data)

    def test_registration_email_exists_returns_400(self):
        """An already registered email is rejected on the email field."""
        url = reverse('register')
        data = {
            'username': 'newuser', 'email': 'test@test.de',
            'password': 'SuperSecret123!',
            'confirmed_password': 'SuperSecret123!',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn('email', response.data)


class LoginTests(APITestCase):
    """Tests for POST /api/login/."""

    def setUp(self):
        """Create the user used for logging in."""
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!',
            email='test@test.de')

    def test_login(self):
        """Valid credentials return the user data and set both cookies."""
        url = reverse('login')
        data = {'username': 'loginuser', 'password': 'SuperSecret123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['user']['username'], 'loginuser')
        self.assertEqual(response.data['user']['email'], 'test@test.de')
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_wrong_password_returns_401(self):
        """A wrong password is rejected with 401."""
        url = reverse('login')
        data = {'username': 'loginuser', 'password': 'wrong_password'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
        self.assertIn('detail', response.data)

    def test_login_wrong_username_returns_401(self):
        """An unknown username is rejected with 401."""
        url = reverse('login')
        data = {'username': 'unknownuser', 'password': 'SuperSecret123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)


class LogoutTests(APITestCase):
    """Tests for POST /api/logout/."""

    def setUp(self):
        """Create a user and log the test client in."""
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!',
            email='test@test.de')
        self.client.post(
            reverse('login'),
            {'username': 'loginuser', 'password': 'SuperSecret123!'},
            format='json',
        )

    def test_logout(self):
        """A logged in user is logged out and both cookies are cleared."""
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')
        self.assertIn('detail', response.data)

    def test_logout_without_login_returns_401(self):
        """A client without cookies cannot log out."""
        client = APIClient()
        response = client.post(reverse('logout'))
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)

    def test_user_already_logged_out_returns_401(self):
        """A blacklisted refresh token is rejected on a second logout."""
        access = self.client.cookies['access_token'].value
        refresh = self.client.cookies['refresh_token'].value
        self.client.post(reverse('logout'))
        self.client.cookies['access_token'] = access
        self.client.cookies['refresh_token'] = refresh
        response = self.client.post(reverse('logout'))
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)


class TokenRefreshTests(APITestCase):
    """Tests for POST /api/token/refresh/."""

    def setUp(self):
        """Create a user and log the test client in."""
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!',
            email='test@test.de')
        self.client.post(
            reverse('login'),
            {'username': 'loginuser', 'password': 'SuperSecret123!'},
            format='json',
        )

    def test_token_refresh(self):
        """A valid refresh cookie yields a new access token cookie."""
        url = reverse('token_refresh')
        response = self.client.post(url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['detail'], 'Token refreshed')
        self.assertIn('access_token', response.cookies)

    def test_token_refresh_without_login_returns_401(self):
        """A client without a refresh cookie is rejected with 401."""
        client = APIClient()
        response = client.post(reverse('token_refresh'))
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
