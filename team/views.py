from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.models import Team, TeamMember
from . import serializers
from .permissions import IsAllowedToEdit, IsAllowedToDelete, IsAllowedToEditMembers


class TeamViewSet(ModelViewSet):
    serializer_class = serializers.TeamSerializer
    queryset = Team.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAllowedToEdit, IsAllowedToDelete]

    def get_queryset(self):
        return Team.objects.filter(member__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.TeamListSerializer
        return self.serializer_class

    @action(
        detail=True,
        methods=["post", "get"],
        serializer_class=serializers.TeamMemberSerializer,
    )
    def members(self, request, pk=None):
        """Action for crud of team members"""
        team = self.get_object()
        if request.method == "GET":
            team_members = TeamMember.objects.filter(team=team)
            serializer = serializers.TeamMemberSerializer(team_members, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            context = {"request": self.request}
            serializer = serializers.TeamMemberSerializer(
                data=request.data, context=context, many=True
            )
            if serializer.is_valid():
                serializer.save(team=team)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "members":
            permission_classes = [IsAuthenticated, IsAllowedToEditMembers]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]
