from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from core.models import Project, Team, TeamMember
from .serializers import ProjectSerializer, ProjectListSerializer


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
        """Checks if user is a team admin of the requested team_id"""
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
        ## Checks for team_id
        team_id = self.request.data.get("team_id", None)
        if not team_id:
            return Response(
                {"detail": "team_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        res = self.check_team_admin(team_id)
        if res:
            return res
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        team_id = self.request.data.get("team_id")
        serializer.save(team_id=team_id)
