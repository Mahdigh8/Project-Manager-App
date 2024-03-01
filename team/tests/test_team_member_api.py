import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Team, TeamMember


def team_member_url(team_id):
    return reverse("team:team-members", args=[team_id])


def create_team(**params):
    payload = {
        "name": "Test team",
        "description": "Team Desc",
        "public_edit": "ALL",
        "privacy_edit": "ALL",
    }
    payload.update(**params)
    return Team.objects.create(**payload)


def create_member(**params):
    return TeamMember.objects.create(**params)


def create_user(**params):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testUserPAss112",
    }
    payload.update(**params)
    return get_user_model().objects.create_user(**params)


class PublicTeamMemberApiTests(TestCase):
    def test_unauthorized_access(self):
        """Test unauthorized team member access"""
        self.client = APIClient()
        team = create_team()
        res = self.client.get(team_member_url(team.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TeamMemberAPITests(TestCase):
    """Private TeamMember API Tests"""

    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user1 = create_user(username="testUser1", email="test1@example.com")
        cls.user2 = create_user(username="testUser2", email="test2@example.com")
        cls.client.force_authenticate(user=cls.user1)
        cls.team = create_team()

    def setUp(self):
        self.client = TeamMemberAPITests.client

    def test_list_team_members(self):
        """Test retrieving team members where user is a member of that team"""
        create_member(user=self.user1, team=self.team, is_admin=True)
        create_member(user=self.user2, team=self.team, is_admin=False)

        res = self.client.get(team_member_url(self.team.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        team_members = TeamMember.objects.filter(team=self.team)
        self.assertEqual(len(team_members), 2)

    def test_list_team_members_not_a_member_fails(self):
        """Test getting list of team members where user is not a member should fail"""
        res = self.client.get(team_member_url(self.team.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_members_to_team_with_admin_role(self):
        """
        Test adding members to team via their email successful
        request is sending via user1 that is team admin
        """
        mem = create_member(user=self.user1, team=self.team, is_admin=True)
        self.assertTrue(mem.is_admin)
        user3 = create_user(username="testUser3", email="test3@example.com")
        payload = json.dumps([{"email": self.user2.email}, {"email": user3.email}])
        res = self.client.post(
            team_member_url(self.team.id), payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        team_members = TeamMember.objects.filter(team=self.team)
        self.assertEqual(len(team_members), 3)

    def test_add_members_to_team_without_admin_role(self):
        """
        Test adding members to team via their email fails
        request is sending via user1 that is not a team admin
        """
        create_member(user=self.user1, team=self.team, is_admin=False)
        payload = json.dumps([{"email": self.user2.email}])
        res = self.client.post(
            team_member_url(self.team.id), payload, content_type="application/json"
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        team_members = TeamMember.objects.filter(team=self.team)
        self.assertEqual(len(team_members), 1)

    def test_add_members_to_team_user_not_team_member(self):
        """
        Test adding members to team via their email fails
        request is sending via user1 that is not a team member
        """
        payload = json.dumps([{"email": self.user2.email}])
        res = self.client.post(
            team_member_url(self.team.id), payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_members_to_team_email_not_exist(self):
        """
        Test adding members to team via their email fails
        email does not exist.
        """
        create_member(user=self.user1, team=self.team, is_admin=True)
        payload = json.dumps([{"email": "Random@email.com"}])
        res = self.client.post(
            team_member_url(self.team.id), payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
