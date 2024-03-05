from rest_framework import serializers
from core.models import Project, Team, Task
from .custom_serializer_fields import TaskDetailHyperlink


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
    team_id = serializers.IntegerField(write_only=True)

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

    def update(self, instance, validated_data):
        team_id = validated_data.pop("team_id", None)
        if team_id:
            team = Team.objects.get(pk=team_id)
            validated_data["team"] = team
        return super().update(instance, validated_data)


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer for listing task objects"""

    assigned_to = serializers.CharField(source="assigned_to.user.username")
    url = TaskDetailHyperlink(view_name="project:task-detail")

    class Meta:
        model = Task
        fields = ["id", "title", "status", "assigned_to", "due_date", "url"]


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for listing task objects"""

    assigned_to = serializers.CharField(source="assigned_to.user.username")
    created_by = serializers.CharField(source="created_by.user.username")

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "status",
            "assigned_to",
            "created_by",
            "created_at",
            "description",
            "due_date",
        ]
