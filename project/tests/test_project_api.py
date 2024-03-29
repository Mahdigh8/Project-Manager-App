from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from core.models import Project, Team, TeamMember
from django.contrib.auth import get_user_model
from rest_framework import status


PROJECT_URL = reverse("project:project-list")


def project_detail_url(project_id):
    return reverse("project:project-detail", args=[project_id])


def create_project(**params):
    return Project.objects.create(**params)


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


class PublicProjectApiTests(TestCase):
    def test_unauthorized_access(self):
        """Test unauthorized project access"""
        self.client = APIClient()
        team = create_team()
        project = create_project(name="Test project", team=team)
        res = self.client.get(project_detail_url(project.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class ProjectAPITests(TestCase):
    """Private Project API Tests"""

    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user1 = create_user(username="testUser1", email="test1@example.com")
        cls.client.force_authenticate(user=cls.user1)
        cls.team = create_team()

    def setUp(self):
        self.client = ProjectAPITests.client

    def test_list_project_limited_to_user(self):
        """Test listing project that the user is part of"""
        create_member(user=self.user1, team=self.team)
        create_project(name="Project 1", team=self.team)
        create_project(name="Project 2", team=self.team)
        ## another project with another team
        ## that user is not a member of that team
        team2 = create_team()
        create_project(name="Project 3", team=team2)

        res = self.client.get(PROJECT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_view_detail_project(self):
        """Test viewing project that the user is a part of"""
        create_member(user=self.user1, team=self.team)
        project = create_project(name="Project 1", team=self.team)

        res = self.client.get(project_detail_url(project.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], project.name)
        self.assertIn(
            reverse("team:team-detail", args=[project.team.id]), res.data["team"]
        )

    def test_view_detail_project_not_allowed(self):
        """Test viewing project that user is not a part of fails"""
        project = create_project(name="Project 1", team=self.team)
        res = self.client.get(project_detail_url(project.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_project_with_team_admin_role(self):
        """Test creating a project with team admin role successful"""
        create_member(user=self.user1, team=self.team, is_admin=True)
        payload = {
            "name": "Test Project 1",
            "team_id": self.team.id,
            "deadline": "2024-03-03",
        }
        res = self.client.post(PROJECT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        projects = Project.objects.all()
        self.assertTrue(projects.exists())
        self.assertEqual(payload["name"], projects[0].name)
        self.assertEqual(payload["deadline"], projects[0].deadline.strftime("%Y-%m-%d"))
        self.assertEqual(payload["team_id"], projects[0].team.id)

    def test_create_project_without_team_admin_role(self):
        """Test creating a project without team admin role fails"""
        create_member(user=self.user1, team=self.team, is_admin=False)
        payload = {
            "name": "Test Project 1",
            "team_id": self.team.id,
        }
        res = self.client.post(PROJECT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        projects = Project.objects.all()
        self.assertFalse(projects.exists())

    def test_create_project_user_not_a_team_member(self):
        """Test creating a project when user is not a team member fails"""
        payload = {
            "name": "Test Project 1",
            "team_id": self.team.id,
        }
        res = self.client.post(PROJECT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        projects = Project.objects.all()
        self.assertFalse(projects.exists())

    def test_partial_update_project_with_team_admin_role(self):
        """Test partial update project with team admin role successful"""
        create_member(team=self.team, user=self.user1, is_admin=True)
        project = create_project(
            name="Project 1", team=self.team, deadline="2024-02-02"
        )
        payload = {
            "name": "Changed name",
            "deadline": "2024-05-25",
        }

        res = self.client.patch(project_detail_url(project.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.name, payload["name"])
        self.assertEqual(project.deadline.strftime("%Y-%m-%d"), payload["deadline"])

    def test_partial_update_project_without_team_admin_role(self):
        """Test partial update project without team admin role fails"""
        create_member(team=self.team, user=self.user1, is_admin=False)
        project = create_project(
            name="Project 1", team=self.team, deadline="2024-02-02"
        )
        payload = {
            "name": "Changed name",
            "deadline": "2024-05-25",
        }

        res = self.client.patch(project_detail_url(project.id), payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        project.refresh_from_db()
        self.assertNotEqual(project.name, payload["name"])
        self.assertNotEqual(project.deadline.strftime("%Y-%m-%d"), payload["deadline"])

    def test_partial_update_changing_project_team(self):
        """
        Test changing the team that is assigned to the project with team admin role.
        the user should be admin in the new team too.
        """
        team2 = create_team(name="Team 2")
        create_member(team=self.team, user=self.user1, is_admin=True)
        create_member(team=team2, user=self.user1, is_admin=True)
        project = create_project(name="Project 1", team=self.team)
        payload = {
            "name": "Changed name",
            "team_id": team2.id,
        }

        res = self.client.patch(project_detail_url(project.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.name, payload["name"])
        self.assertEqual(project.team.id, payload["team_id"])

    def test_delete_project_with_team_admin_role(self):
        """Test deleting project with team admin role successful"""
        create_member(team=self.team, user=self.user1, is_admin=True)
        project = create_project(name="Project 1", team=self.team)
        res = self.client.delete(project_detail_url(project.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        qs = Project.objects.filter(pk=project.id)
        self.assertFalse(qs.exists())

    def test_delete_project_without_team_admin_role(self):
        """Test deleting project without team admin role fails"""
        create_member(team=self.team, user=self.user1, is_admin=False)
        project = create_project(name="Project 1", team=self.team)
        res = self.client.delete(project_detail_url(project.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        qs = Project.objects.filter(pk=project.id)
        self.assertTrue(qs.exists())
