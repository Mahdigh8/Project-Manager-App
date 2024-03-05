import time
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


class TestProjectModel(TestCase):
    def setUp(self):
        team_payload = {
            "name": "Test team",
            "public_edit": "ADMIN",
        }
        self.team = models.Team.objects.create(**team_payload)

    def test_create_project(self):
        """Test creating a project object"""
        payload = {
            "name": "Test project",
            "team": self.team,
            "deadline": "2024-04-26",
        }
        project = models.Project.objects.create(**payload)
        self.assertEqual(project.name, payload["name"])
        self.assertEqual(project.description, "")
        self.assertEqual(project.team, payload["team"])
        self.assertEqual(project.deadline, payload["deadline"])


class TestTaskModel(TestCase):
    def test_create_task(self):
        """Test creating a task"""
        user1 = get_user_model().objects.create_user(
            email="test1@example.com", username="TestUser1", password="TestPAss123"
        )
        user2 = get_user_model().objects.create_user(
            email="test2@example.com", username="TestUser2", password="TestPAss123"
        )
        team_payload = {
            "name": "Test team",
            "public_edit": "ADMIN",
        }
        team = models.Team.objects.create(**team_payload)
        member1 = models.TeamMember.objects.create(team=team, user=user1, is_admin=True)
        member2 = models.TeamMember.objects.create(
            team=team, user=user2, is_admin=False
        )
        project = models.Project.objects.create(name="Project 1", team=team)
        payload = {
            "title": "Task 1",
            "project": project,
            "assigned_to": member2,
            "created_by": member1,
            "due_date": time.strftime("%Y-%m-%d %H:%M:%S%z"),
        }
        task = models.Task.objects.create(**payload)
        self.assertEqual(task.title, payload["title"])
        self.assertEqual(task.description, "")
        self.assertEqual(task.project, payload["project"])
        self.assertEqual(task.assigned_to, payload["assigned_to"])
        self.assertEqual(task.created_by, payload["created_by"])
        self.assertEqual(task.due_date, payload["due_date"])
        self.assertEqual(task.status, "TODO")
