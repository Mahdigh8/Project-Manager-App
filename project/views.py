from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from core.models import Project, TeamMember
from .serializers import (
    ProjectSerializer,
    ProjectListSerializer,
    TaskListSerializer,
    TaskSerializer,
)
from .permission import IsAllowedToUpdateOrDelete


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        else:
            return self.serializer_class

    def get_queryset(self):
        return self.queryset.filter(team__member__user=self.request.user)

    def check_team_admin(self, team_id):
        """
        Checks if user is a team admin of the requested team_id
        because we want to send an appropriate status code when
        team_id is invalid or user is not a team admin we do this
        check in view and not in the serializer despite the fact
        that it is a data validation.
        """
        ## Check if user is team member
        try:
            member = get_object_or_404(
                TeamMember, team__id=team_id, user=self.request.user
            )
        except:
            return Response(
                {"detail": "Team id not found."}, status=status.HTTP_404_NOT_FOUND
            )
        ## Check if user is team admin
        if not member.is_admin:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def create(self, request, *args, **kwargs):
        ## Checks for user to be a team admin of the requested team_id
        team_id = self.request.data.get("team_id", None)
        if not team_id:
            return Response(
                {"detail": "team_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        res = self.check_team_admin(team_id)
        if res:
            return res
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Checks for user to be a team admin of the requested team_id"""
        team_id = self.request.data.get("team_id", None)
        if team_id:
            res = self.check_team_admin(team_id)
            if res:
                return res
        return super().update(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["get", "post"],
        url_path="task",
        serializer_class=TaskListSerializer,
    )
    def task_list(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            queryset = project.tasks.all().order_by("-created_at")
            serializer = TaskListSerializer(
                queryset, context={"request": request}, many=True
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get", "patch", "delete"],
        url_path="task/<int:task_id>",
        serializer_class=TaskSerializer,
    )
    def task_detail(self, request, pk=None, task_id=None):
        project = self.get_object()
        try:
            task = get_object_or_404(project.tasks, pk=task_id)
        except:
            return Response(
                {"detail": "Task id not found."}, status=status.HTTP_404_NOT_FOUND
            )
        if request.method == "GET":
            serializer = TaskSerializer(task)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsAllowedToUpdateOrDelete]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]
