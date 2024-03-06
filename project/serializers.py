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

    ## this field is for representation only
    assignee = serializers.CharField(source="assigned_to.user.username", read_only=True)
    created_by = serializers.CharField(
        source="created_by.user.username", read_only=True
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "status",
            "assigned_to",
            "assignee",
            "created_by",
            "created_at",
            "description",
            "due_date",
        ]
        extra_kwargs = {
            "assigned_to": {"write_only": True, "required": True},
        }

    def _validate_assigned_to(self, validated_data):
        ## Check if assigned_to member is a member of the project team
        project = validated_data.get("project", None)
        assigned_to = validated_data.get("assigned_to", None)
        if not project.team.member.filter(pk=assigned_to.id).exists():
            raise serializers.ValidationError(
                "assigned_to id is not a member of this project"
            )

    def create(self, validated_data):
        self._validate_assigned_to(validated_data)
        project = validated_data.get("project", None)
        request = self.context.get("request")
        created_by = project.team.member.get(user=request.user)
        validated_data["created_by"] = created_by
        return super().create(validated_data)

    def update(self, instance, validated_data):
        assigned_to = validated_data.get("assigned_to", None)
        if assigned_to:
            self._validate_assigned_to(validated_data)
        validated_data.pop("project", None)
        return super().update(instance, validated_data)
