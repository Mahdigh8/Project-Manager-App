from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.serializers import UserSerializer


USER_PROFILE_URL = reverse("user:profile")
CHANGE_PASSWORD_URL = reverse("user:password-change")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PrivateUserAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user_payload = {
            "email": "test@example.com",
            "username": "testuser1",
            "password": "Test@user123",
        }
        cls.user = create_user(**cls.user_payload)
        cls.client.force_authenticate(user=cls.user)

    def setUp(self):
        self.client = PrivateUserAPITests.client

    def test_retrieve_profile_success(self):
        """Test retrieving user profile"""
        res = self.client.get(USER_PROFILE_URL)
        serializer = UserSerializer(self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_post_method_not_allowed(self):
        """Test using post method on User profile view is not allowed"""
        res = self.client.post(USER_PROFILE_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user profile"""
        payload = {
            "username": "changedUsername",
            "first_name": "changedFirstName",
            "last_name": "changedLastName",
        }
        res = self.client.patch(USER_PROFILE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, payload["username"])
        self.assertEqual(self.user.first_name, payload["first_name"])
        self.assertEqual(self.user.last_name, payload["last_name"])

    def test_change_password_successful(self):
        """Test change password successful"""
        payload = {
            "old_password": self.user_payload["password"],
            "new_password1": "NewPass123",
            "new_password2": "NewPass123",
        }
        res = self.client.post(CHANGE_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["new_password1"]))

    def test_change_password_with_invalid_old_password(self):
        """Test change password with invalid old password"""
        payload = {
            "old_password": "invalid_old_password",
            "new_password1": "NewPass123",
            "new_password2": "NewPass123",
        }
        res = self.client.post(CHANGE_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(payload["new_password1"]))
