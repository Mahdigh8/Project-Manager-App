from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.models import Team, TeamMember
from . import serializers
from .permissions import (
    IsAllowedToEdit,
    IsAllowedToDelete,
    IsAllowedToAddOrEditMembers,
    IsAllowedToRemoveMembers,
)


class TeamViewSet(ModelViewSet):
    """
    Viewset for list, retrive, create, update and delete team objects
    in addition two actions added to list team members, add and update
    multiple team members and remove team members.
    """

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
        methods=["post", "get", "patch"],
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
            serializer = serializers.TeamMemberSerializer(data=request.data, many=True)
            if serializer.is_valid():
                serializer.save(team=team)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == "PATCH":
            team_members = TeamMember.objects.filter(team=team)
            serializer = serializers.TeamMemberSerializer(
                team_members, data=request.data, many=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        url_path="remove/<int:member_id>",
        methods=["delete"],
    )
    def remove_member(self, request, pk=None, member_id=None):
        if request.method == "DELETE":
            team = self.get_object()
            ## only members of this team can be remove
            queryset = TeamMember.objects.filter(team=team)
            try:
                instance = get_object_or_404(queryset, pk=member_id)
                ## checks permission to remove member
                permission = IsAllowedToRemoveMembers()
                if not permission.has_object_permission(
                    self.request, self, instance, team=team
                ):
                    return Response(
                        {
                            "detail": "You do not have permission to perform this action."
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "members":
            permission_classes = [IsAuthenticated, IsAllowedToAddOrEditMembers]
        elif self.action == "remove_member":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]
