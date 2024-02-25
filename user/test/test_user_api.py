from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:register")
TOKEN_URL = reverse("user:token")


def create_user(**params):
    payload = {
        "email": "test@example.com",
        "username": "testuser1",
        "password": "Test@user123",
    }
    payload.update(**params)
    return get_user_model().objects.create_user(**payload)


class PublicUserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid credentials"""
        payload = {
            "email": "test@example.com",
            "username": "testuser1",
            "password": "Test@user123",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.get(
            username=payload["username"], email=payload["email"]
        )
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_exists(self):
        """Test creating user with an existing email fails"""
        payload = {
            "email": "test@example.com",
            "username": "testuser1",
            "password": "Test@user123",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        num_user = get_user_model().objects.all().count()
        self.assertEqual(num_user, 1)

    def test_create_token_for_user(self):
        """Test create token for user successful"""
        payload = {
            "email": "test@example.com",
            "password": "Test@user123",
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)

    def test_create_token_invalid_credentials(self):
        """Test create token with invalid credentials fails"""
        payload = {
            "email": "test@example.com",
            "password": "Test@user123",
        }
        create_user(**payload)
        res = self.client.post(
            TOKEN_URL,
            {
                "email": payload["email"],
                "password": "WrongPassword",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", res.data)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exist"""
        payload = {
            "email": "test@example.com",
            "password": "Test@user123",
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", res.data)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        payload = {
            "email": "",
            "password": "Test@user123",
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", res.data)

    def test_retrieve_user_unauthorized(self):
        pass
