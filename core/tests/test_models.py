from django.test import TestCase
from core import models
from django.contrib.auth import get_user_model


class TestUserModel(TestCase):
    def test_create_user_with_email(self):
        """Test create user with email successful"""
        payload = {
            "email": "test@example.com",
            "username": "testuser1",
            "password": "testpass123",
        }
        user = get_user_model().objects.create_user(**payload)
        self.assertEqual(user.email, payload["email"])
        self.assertEqual(user.username, payload["username"])
        self.assertTrue(user.check_password(payload["password"]))
