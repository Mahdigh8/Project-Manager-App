import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Team, TeamMember


def team_member_url(team_id):
    return reverse("team:team-members", args=[team_id])


def team_member_remove_url(team_id, member_id):
    return reverse("team:remove-member", kwargs={"pk": team_id, "member_id": member_id})


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

    def test_partial_update_team_members_with_admin_role(self):
        """
        Test partial update team members
        only team admins can update team members role
        """
        create_member(user=self.user1, team=self.team, is_admin=True)
        member2 = create_member(user=self.user2, team=self.team, is_admin=False)
        payload = json.dumps([{"id": member2.id, "is_admin": True}])
        res = self.client.patch(
            team_member_url(self.team.id), payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        member2.refresh_from_db()
        self.assertTrue(member2.is_admin)

    def test_partial_update_team_members_without_admin_role(self):
        """
        Test partial update team members without admin role fails
        """
        create_member(user=self.user1, team=self.team, is_admin=False)
        member2 = create_member(user=self.user2, team=self.team, is_admin=False)
        payload = json.dumps([{"id": member2.id, "is_admin": True}])
        res = self.client.patch(
            team_member_url(self.team.id), payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        member2.refresh_from_db()
        self.assertFalse(member2.is_admin)

    def test_partial_update_team_member_id_not_exist(self):
        """
        Test partial update team members with admin role
        with an id that does not exist fails
        """
        create_member(user=self.user1, team=self.team, is_admin=True)
        payload = json.dumps([{"id": 85, "is_admin": True}])
        res = self.client.patch(
            team_member_url(self.team.id), payload, content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_team_member_with_admin_role(self):
        """Test deleting a team member with admin role successful"""
        create_member(user=self.user1, team=self.team, is_admin=True)
        member2 = create_member(user=self.user2, team=self.team, is_admin=False)
        res = self.client.delete(team_member_remove_url(self.team.id, member2.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TeamMember.objects.filter(id=member2.id).exists())

    def test_delete_other_team_members_without_admin_role(self):
        """Test deleting other team members without admin role fails"""
        create_member(user=self.user1, team=self.team, is_admin=False)
        member2 = create_member(user=self.user2, team=self.team, is_admin=False)
        res = self.client.delete(team_member_remove_url(self.team.id, member2.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(TeamMember.objects.filter(id=member2.id).exists())

    def test_user_leaving_team(self):
        """
        Test leaving team successful
        this is the same endpoint but because the user want
        to remove himself from the team it should be successful
        """
        ## user does not have admin role
        member = create_member(user=self.user1, team=self.team, is_admin=False)
        res = self.client.delete(team_member_remove_url(self.team.id, member.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TeamMember.objects.filter(id=member.id).exists())
