from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Team, TeamMember
from team.serializers import TeamSerializer


TEAMS_URL = reverse("team:team-list")


def team_detail_url(team_id):
    return reverse("team:team-detail", args=[team_id])


def create_team(**params):
    payload = {
        "name": "Test team",
        "description": "Team Desc",
    }
    payload.update(**params)
    return Team.objects.create(**payload)


class PublicTeamApiTests(TestCase):
    """Test unauthenticated team API access"""

    def test_auth_required(self):
        """Test that authentication is required"""
        self.client = APIClient()
        res = self.client.get(TEAMS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestTeamAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = get_user_model().objects.create_user(
            email="test@example.com", username="testUser1", password="TestPass123"
        )
        cls.client.force_authenticate(user=cls.user)

    def test_list_teams_limited_to_user(self):
        """Test retrieving teams that user is a member of them"""
        team1 = create_team()
        TeamMember.objects.create(user=self.user, team=team1)
        ## create another user and assign it to a team
        other_user = get_user_model().objects.create(
            email="other@example.com", username="otherUser2", password="otherPass123"
        )
        team2 = create_team()
        TeamMember.objects.create(user=other_user, team=team2)

        res = self.client.get(TEAMS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user_teams = Team.objects.filter(member__user=self.user)
        serializer = TeamSerializer(user_teams, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(user_teams), 1)

    def test_view_team_detail(self):
        """Test viewing a team detail that user is a member of"""
        team = create_team()
        TeamMember.objects.create(user=self.user, team=team)
        res = self.client.get(team_detail_url(team.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = TeamSerializer(team)
        self.assertEqual(res.data, serializer.data)

    ## Maybe not necessery bacause of setting get_queryset in viewset
    def test_view_team_detail(self):
        """Test viewing a team detail that user is not a member should fails"""
        team = create_team()
        res = self.client.get(team_detail_url(team.id))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_basic_team(self):
        """Test creating a team"""
        payload = {
            "name": "Test team",
            "description": "Team Desc",
        }
        res = self.client.post(TEAMS_URL, payload)

        team = Team.objects.get(id=res.data["id"])
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(team.name, payload["name"])
        self.assertEqual(team.description, payload["description"])
        ## checks that with team creation user should
        ## be added to the team members as admin automatically
        team_member = TeamMember.objects.get(team=team, user=self.user)
        self.assertIsNotNone(team_member)
        self.assertTrue(team_member.is_admin)

    def test_create_team_with_members(self):
        """Test creating a team with members"""
        user2 = get_user_model().objects.create(
            email="other@example.com", username="otherUser2", password="otherPass123"
        )
        payload = {
            "name": "Test team",
            "description": "Team Desc",
            "members": [user2.username],
        }
        res = self.client.post(TEAMS_URL, payload)

        team = Team.objects.get(id=res.data["id"])
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ## checks added members to the team
        ## team creator automatically added to members
        team_members = TeamMember.objects.filter(team=team)
        self.assertEqual(team_members.count(), 2)
        self.assertIn(self.user, team_members)
        self.assertIn(user2, team_members)
        ## user2 should be a normal member not an admin
        user2_member = team_members.filter(user=user2)
        self.assertFalse(user2_member.is_admin)

    def test_partial_update_team_with_admin_role(self):
        """Test partial update team with a user that has admin role in the team"""
        team = create_team()
        TeamMember.objects.create(user=self.user, team=team, is_admin=True)
        payload = {
            "name": "Changed Name",
            "public_edit": "ADMIN",
            "privacy_edit": "ALL",
        }
        res = self.client.patch(team_detail_url(team.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        team.refresh_from_db()
        self.assertEqual(team.name, payload["name"])
        self.assertEqual(team.public_edit, payload["public_edit"])
        self.assertEqual(team.privacy_edit, payload["privacy_edit"])

    def test_partial_update_team_without_admin_role(self):
        """
        Test partial update team with a user that does not have
        an admin role in the team.
        """
        ## set public edit to all that all members can change team name and description
        team = create_team(public_edit="ALL")
        TeamMember.objects.create(user=self.user, team=team, is_admin=False)
        payload = {
            "description": "Changed Desc",
        }
        res = self.client.patch(team_detail_url(team.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        team.refresh_from_db()
        self.assertEqual(team.description, payload["description"])

    def test_partial_update_team_edit_permission_denied(self):
        """
        Test partial update team with a user that does not have
        an admin role in the team and public_edit field is set to
        only admins can change name and description
        """
        ## set public edit to admin only that only admins can change team name and description
        team = create_team(public_edit="ADMIN")
        TeamMember.objects.create(user=self.user, team=team, is_admin=False)
        payload = {
            "name": "changed name",
        }
        res = self.client.patch(team_detail_url(team.id), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_team_edit_fields_fails(self):
        """
        Test partial update team with a user that does not have
        an admin role in the team and trys to edit public_edit
        and privacy_edit fields that fails.
        """
        team = create_team()
        TeamMember.objects.create(user=self.user, team=team, is_admin=False)
        payload = {
            "public_edit": "ALL",
            "privacy_edit": "ADMIN",
        }
        res = self.client.patch(team_detail_url(team.id), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_team_not_a_member(self):
        """Test deleting team with user that is not a member of team"""
        team = create_team()
        res = self.client.delete(team_detail_url(team.id))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Team.objects.filter(id=team.id).exists())

    def test_delete_team_with_admin_role(self):
        """
        Test deleting team with admin role
        where privacy_edit is set to Admin only
        """
        team = create_team()
        TeamMember.objects.create(user=self.user, team=team, is_admin=True)
        res = self.client.delete(team_detail_url(team.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Team.objects.filter(id=team.id).exists())

    def test_delete_team_without_admin_role(self):
        """
        Test deleting team without admin role
        where privacy_edit is set to All members
        """
        team = create_team()
        TeamMember.objects.create(user=self.user, team=team, is_admin=False)
        res = self.client.delete(team_detail_url(team.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Team.objects.filter(id=team.id).exists())
