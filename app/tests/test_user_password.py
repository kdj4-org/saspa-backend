from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
import uuid

from app.models import PasswordResetToken
from app.serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer

User = get_user_model()

EXPIRY_MINUTES = 30

class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            nombre='Juan Pérez',
            password='old_password'
        )

    def test_password_reset_request_valid_email(self):
        url = reverse('password-reset-request')
        response = self.client.post(url, {'email': self.user.email})
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_request_invalid_email(self):
        url = reverse('password-reset-request')
        response = self.client.post(url, {'email': 'nonexistent@example.com'})
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_request_invalid_payload(self):
        url = reverse('password-reset-request')
        response = self.client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_expired_token(self):
        expired_token = PasswordResetToken.objects.create(
            usuario=self.user,
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        url = reverse('password-reset-confirm', kwargs={'token': str(expired_token.token)})
        response = self.client.post(url, {'new_password': 'new_secure_password'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_invalid_payload(self):
        token = PasswordResetToken.objects.create(
            usuario=self.user,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        url = reverse('password-reset-confirm', kwargs={'token': str(token.token)})
        response = self.client.post(url, {}) 
        assert response.status_code == status.HTTP_400_BAD_REQUEST