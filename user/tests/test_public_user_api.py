import re
from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:register")
TOKEN_URL = reverse("user:token")
RESET_PASSWORD_URL = reverse("user:password-reset")
RESET_PASSWORD_CONFIRM_URL = reverse("user:password-reset-confirm")
CHANGE_PASSWORD_URL = reverse("user:password-change")


def create_user(**params):
    payload = {
        "email": "test@example.com",
        "username": "testuser1",
        "password": "Test@user123",
    }
    payload.update(**params)
    return get_user_model().objects.create_user(**payload)


def get_reset_password_url(body):
    """get reset password url from email body"""
    pattern = r"(https|http):\/\/testserver\/reset\/\w{2,}\/(\w+)-(\w+)\/"
    match_obj = re.search(pattern, body)
    if match_obj is not None:
        url = match_obj.group()
    return url


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

    def test_reset_password_send_email_not_existed(self):
        """Test view should not send password reset link to an email not existed in database"""
        payload = {"email": "test@example.com"}
        res = self.client.post(RESET_PASSWORD_URL, payload)
        ## should not respond with a 400 bad request because
        ## we don't want to reveal that a user with this email
        ## exist in our database or not.
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_password_send_email_existed(self):
        """Test sending an email to a user that exist in our database"""
        payload = {"email": "test@example.com"}
        create_user(**payload)
        res = self.client.post(RESET_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        reset_url = get_reset_password_url(mail.outbox[0].body)
        self.assertIsNotNone(reset_url)

    def test_reset_password_confirm_successful(self):
        """Test confirming rest password with valid uid and token successful"""
        ## creating a user and send a password reset email
        payload = {"email": "test@example.com"}
        user = create_user(**payload)
        self.client.post(RESET_PASSWORD_URL, payload)
        ## get reset link from email body and split token and uid part
        reset_url = get_reset_password_url(mail.outbox[0].body)
        token = reset_url.split("/")[-2]
        uid = reset_url.split("/")[-3]
        ## send payload to reset confirm url
        payload = {
            "token": token,
            "uid": uid,
            "new_password1": "NewPass123",
            "new_password2": "NewPass123",
        }
        res = self.client.post(RESET_PASSWORD_CONFIRM_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password(payload["new_password1"]))

    def test_reset_password_confirm_with_invalid_token_and_uid(self):
        """Test confirming rest password with invalid uid and token fails"""
        payload = {
            "token": "invalid_token",
            "uid": "invalid_uid",
            "new_password1": "NewPass123",
            "new_password2": "NewPass123",
        }
        res = self.client.post(RESET_PASSWORD_CONFIRM_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated_fails(self):
        """Test changing password when user is not authenticated fails"""
        payload = {
            "old_password": "oldPass123",
            "new_password1": "NewPass123",
            "new_password2": "NewPass123",
        }
        res = self.client.post(CHANGE_PASSWORD_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
