from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings

Usuario = get_user_model()

class RegisterUserViewTest(APITestCase):
    def test_register_user_success(self):
        url = reverse('register')
        data = {
            'email': 'test@example.com',
            'nombre': 'Test User',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'User registered successfully')
        self.assertIn('Authorization', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], data['email'])
        self.assertEqual(response.data['user']['nombre'], data['nombre'])
        self.assertEqual(response.data['user']['rol'], 'cliente')
        self.assertIsNotNone(response.data['Authorization'])

        self.assertTrue(Usuario.objects.filter(email=data['email']).exists())
        user = Usuario.objects.get(email=data['email'])
        self.assertTrue(user.check_password(data['password']))

        token = response.data['Authorization']
        self.assertIsNotNone(token)
        try:
            jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        except Exception as e:
            self.fail(f"Token decoding failed: {e}")

    def test_register_user_missing_email(self):
        url = reverse('register')
        data = {
            'nombre': 'Test User',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_user_missing_nombre(self):
        url = reverse('register')
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', response.data)

    def test_register_user_missing_password(self):
        url = reverse('register')
        data = {
            'email': 'test@example.com',
            'nombre': 'Test User',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_user_invalid_email_format(self):
        url = reverse('register')
        data = {
            'email': 'invalid-email',
            'nombre': 'Test User',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_user_duplicate_email(self):
        url = reverse('register')
        existing_user_data = {
            'email': 'existing@example.com',
            'nombre': 'Existing User',
            'password': 'existingpassword'
        }
        Usuario.objects.create_user(**existing_user_data)
        data = {
            'email': 'existing@example.com',
            'nombre': 'Another User',
            'password': 'newpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

class LoginViewTest(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'testlogin@example.com',
            'nombre': 'Test Login User',
            'password': 'loginpassword'
        }
        self.user = Usuario.objects.create_user(**self.user_data)
        self.login_url = reverse('login')

    def test_login_success(self):
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Authorization', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])
        self.assertEqual(response.data['user']['nombre'], self.user_data['nombre'])
        self.assertEqual(response.data['user']['rol'], 'cliente')
        self.assertIsNotNone(response.data['Authorization'])

        token = response.data['Authorization']
        self.assertIsNotNone(token)
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            self.assertEqual(payload['user_id'], self.user.id)
            self.assertEqual(payload['email'], self.user.email)
            self.assertEqual(payload['rol'], self.user.rol)
            self.assertIsNotNone(payload['exp'])
            self.assertIsNotNone(payload['iat'])
        except Exception as e:
            self.fail(f"Token decoding failed: {e}")

    def test_login_invalid_credentials_wrong_password(self):
        data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
        self.assertNotIn('Authorization', response.data)
        self.assertNotIn('user', response.data)

    def test_login_invalid_credentials_user_not_found(self):
        data = {
            'email': 'nonexistent@example.com',
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
        self.assertNotIn('Authorization', response.data)
        self.assertNotIn('user', response.data)

    def test_login_missing_email(self):
        data = {
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        data = {
            'email': self.user_data['email']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)