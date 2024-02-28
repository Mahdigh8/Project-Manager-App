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


class TestTeamModel(TestCase):
    def test_create_team(self):
        """Test create team"""
        payload = {
            "name": "Test team",
            "public_edit": "ADMIN",
        }
        team = models.Team.objects.create(**payload)
        self.assertEqual(team.name, payload["name"])
        self.assertEqual(team.description, "")
        self.assertEqual(team.public_edit, payload["public_edit"])
        self.assertEqual(team.privacy_edit, "ALL")


class TestTeamMemberModel(TestCase):
    def setUp(self):
        team_payload = {
            "name": "Test team",
            "public_edit": "ADMIN",
        }
        user_payload = {
            "email": "test@example.com",
            "username": "testuser1",
            "password": "testpass123",
        }
        self.team = models.Team.objects.create(**team_payload)
        self.user = get_user_model().objects.create_user(**user_payload)

    def test_create_team_member(self):
        """Test create a team member"""
        member = models.TeamMember.objects.create(user=self.user, team=self.team)

        self.assertEqual(member.user, self.user)
        self.assertEqual(member.team, self.team)
        self.assertFalse(member.is_admin)

    def test_create_team_member_already_exist(self):
        """
        Test creating a team member that already exist in the team fails
        team members should be unique together on user and team
        """
        models.TeamMember.objects.create(user=self.user, team=self.team)
        with self.assertRaises(BaseException):
            models.TeamMember.objects.create(user=self.user, team=self.team)
