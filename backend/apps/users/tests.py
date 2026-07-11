from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock

from apps.users.models import User


class AuthTests(APITestCase):
    def test_register_success(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
        }
        response = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["username"], "testuser")
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_password_mismatch(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "password2": "Different1!",
        }
        response = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="testuser", password="TestPass123!")
        data = {
            "username": "testuser",
            "email": "other@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
        }
        response = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        user = User.objects.get(username="testuser")
        self.assertTrue(user.is_online)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "nobody", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_authenticated(self):
        user = User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_me_unauthenticated(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.users.views.RefreshToken.blacklist")
    def test_logout_success(self, mock_blacklist):
        user = User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        self.client.force_authenticate(user=user)
        login_resp = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "TestPass123!"},
            format="json",
        )
        refresh_token = login_resp.data["refresh"]

        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertFalse(user.is_online)

    def test_token_refresh(self):
        user = User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        login_resp = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "TestPass123!"},
            format="json",
        )
        refresh_token = login_resp.data["refresh"]

        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
