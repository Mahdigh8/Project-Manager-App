from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from user.serializers import UserSerializer


USER_PROFILE_URL = reverse("user:profile")


def create_user(**params):
    payload = {
        "email": "test@example.com",
        "username": "testuser1",
        "password": "Test@user123",
    }
    payload.update(**params)
    return get_user_model().objects.create_user(**payload)


class PrivateUserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

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
