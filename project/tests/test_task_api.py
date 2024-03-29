import time
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from core.models import Task, Project, Team, TeamMember
from django.contrib.auth import get_user_model
from rest_framework import status


def task_detail_url(project_id, task_id):
    return reverse("project:task-detail", kwargs={"pk": project_id, "task_id": task_id})


def task_url(project_id):
    return reverse("project:task-list", kwargs={"pk": project_id})


def create_task(**params):
    return Task.objects.create(**params)


def create_project(**params):
    payload = {
        "name": "Project 1",
    }
    payload.update(**params)
    return Project.objects.create(**payload)


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


class TaskAPITests(TestCase):
    """Private Task API Tests"""

    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user1 = create_user(username="testUser1", email="test1@example.com")
        cls.user2 = create_user(username="testUser2", email="test2@example.com")
        cls.client.force_authenticate(user=cls.user1)
        cls.team = create_team()
        cls.member1 = create_member(user=cls.user1, team=cls.team, is_admin=True)
        cls.member2 = create_member(user=cls.user2, team=cls.team, is_admin=False)
        cls.project = create_project(team=cls.team)

    def setUp(self):
        self.client = TaskAPITests.client

    def test_list_task_limited_to_project(self):
        """Test listing tasks limited to project"""
        payload = {
            "title": "Task Title",
            "project": self.project,
            "assigned_to": self.member2,
            "created_by": self.member1,
        }
        create_task(**payload)
        create_task(**payload)

        project2 = create_project(team=self.team)
        payload.update(project=project2)
        create_task(**payload)

        res = self.client.get(task_url(self.project.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_view_task_detail(self):
        """Test viewing task details where user is a team member of project"""
        payload = {
            "title": "Task Title",
            "project": self.project,
            "assigned_to": self.member2,
            "created_by": self.member1,
        }
        task = create_task(**payload)
        res = self.client.get(task_detail_url(self.project.id, task.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(task.title, res.data["title"])
        self.assertIn("assignee", res.data)
        self.assertIn("created_by", res.data)

    def test_create_task_in_project(self):
        """Test creating task in project"""
        payload = {
            "title": "Task 1",
            "assigned_to": self.member2.pk,
            "due_date": time.strftime("%Y-%m-%d %H:%M:%S%z"),
        }
        res = self.client.post(task_url(self.project.id), payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tasks = Task.objects.all()
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks[0].assigned_to, self.member2)
        self.assertEqual(tasks[0].created_by, self.member1)
        self.assertEqual(tasks[0].project, self.project)

    def test_partial_update_task(self):
        """Test updating task"""
        payload = {
            "title": "Task Title",
            "project": self.project,
            "assigned_to": self.member2,
            "created_by": self.member1,
        }
        task = create_task(**payload)
        user3 = create_user(username="testUser3", email="test3@example.com")
        member3 = create_member(user=user3, team=self.team)
        payload = {
            "title": "Changed Title",
            "description": "Some Description",
            "assigned_to": member3.id,
            "due_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "DONE",
        }
        res = self.client.patch(task_detail_url(self.project.id, task.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, payload["title"])
        self.assertEqual(task.description, payload["description"])
        self.assertEqual(task.status, payload["status"])
        self.assertEqual(task.assigned_to, member3)
        self.assertEqual(
            task.due_date.strftime("%Y-%m-%d %H:%M:%S"), payload["due_date"]
        )

    def test_partial_update_task_with_invalid_assigned_to(self):
        """Test updating task with invalid assigned_to pk fails"""
        payload = {
            "title": "Task Title",
            "project": self.project,
            "assigned_to": self.member2,
            "created_by": self.member1,
        }
        task = create_task(**payload)
        payload = {
            "assigned_to": 46,
        }
        res = self.client.patch(task_detail_url(self.project.id, task.id), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        task.refresh_from_db()
        self.assertNotEqual(task.assigned_to, payload["assigned_to"])

    def test_partial_update_task_with_not_allowed_fields(self):
        """Test updating not allowed fields of task object fails"""
        payload = {
            "title": "Task Title",
            "project": self.project,
            "assigned_to": self.member2,
            "created_by": self.member1,
        }
        task = create_task(**payload)
        payload = {
            "created_by": self.member2,
        }
        res = self.client.patch(task_detail_url(self.project.id, task.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertNotEqual(task.created_by, payload["created_by"])

    def test_delete_task(self):
        """Test deleting task"""
        payload = {
            "title": "Task Title",
            "project": self.project,
            "assigned_to": self.member2,
            "created_by": self.member1,
        }
        task = create_task(**payload)
        res = self.client.delete(task_detail_url(self.project.id, task.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.all().exists())
