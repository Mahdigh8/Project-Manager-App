from rest_framework import serializers
from core.models import Project, Team


class ProjectListSerializer(serializers.Serializer):
    """Serializer for listing projects"""

    url = serializers.HyperlinkedIdentityField(
        view_name="project:project-detail", read_only=True
    )
    name = serializers.CharField()


class ProjectSerializer(serializers.ModelSerializer):
    team = serializers.HyperlinkedRelatedField(
        view_name="team:team-detail", read_only=True
    )
    team_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "team_id", "description", "team", "deadline"]
        extra_kwargs = {"description": {"required": False}}

    def create(self, validated_data):
        team_id = validated_data.pop("team_id", None)
        team = Team.objects.get(pk=team_id)
        validated_data["team"] = team
        project = Project.objects.create(**validated_data)
        return project
