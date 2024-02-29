from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Team
from . import serializers
from .permissions import IsAllowedToEdit, IsAllowedToDelete


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
