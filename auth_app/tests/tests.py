from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()

class RegistrationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!', email='test@test.de')

    def test_registration(self):
        url = reverse('register')
        data = {
            'username': 'newuser', 'email': 'new@test.de',
            'password': 'SuperSecret123!', 'confirmed_password': 'SuperSecret123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["detail"], "User created successfully!")
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch_returns_400(self):
        url = reverse('register')
        data = {
            'username': 'newuser', 'email': 'new@test.de',
            'password': 'SuperSecret123!', 'confirmed_password': 'differentpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn('confirmed_password', response.data)

    def test_registration_email_exists_returns_400(self):
        url = reverse('register')
        data = {
            'username': 'newuser', 'email': 'test@test.de',
            'password': 'SuperSecret123!', 'confirmed_password': 'SuperSecret123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn('email', response.data)


class LoginTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!', email='test@test.de')

    def test_login(self):
        url = reverse('login')
        data = {'username': 'loginuser', 'password': 'SuperSecret123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['user']['username'], 'loginuser')
        self.assertEqual(response.data['user']['email'], 'test@test.de')
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_wrong_password_returns_401(self):
        url = reverse('login')
        data = {'username': 'loginuser', 'password': 'wrong_password'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
        self.assertIn('detail', response.data)

    def test_login_wrong_username_returns_401(self):
        url = reverse('login')
        data = {'username': 'unknownuser', 'password': 'SuperSecret123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)


class LogoutTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!', email='test@test.de')
        self.client.post(
            reverse('login'),
            {'username': 'loginuser', 'password': 'SuperSecret123!'},
            format='json',
        )

    def test_logout(self):
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')
        self.assertIn('detail', response.data)

    def test_logout_without_login_returns_401(self):
        client = APIClient()          
        response = client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)

    def test_user_already_logged_out_returns_401(self):
        access = self.client.cookies['access_token'].value
        refresh = self.client.cookies['refresh_token'].value
        self.client.post(reverse('logout'))              
        self.client.cookies['access_token'] = access    
        self.client.cookies['refresh_token'] = refresh
        response = self.client.post(reverse('logout'))   
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)


class TokenRefreshTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='SuperSecret123!', email='test@test.de')
        self.client.post(
            reverse('login'),
            {'username': 'loginuser', 'password': 'SuperSecret123!'},
            format='json',
        )

    def test_token_refresh(self):
        url = reverse('token_refresh')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['detail'], 'Token refreshed')
        self.assertIn('access_token', response.cookies)

    def test_token_refresh_without_login_returns_401(self):
        client = APIClient()          
        response = client.post(reverse('token_refresh'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)



