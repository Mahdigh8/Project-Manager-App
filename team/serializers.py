from rest_framework import serializers
from core.models import Team, TeamMember
from django.contrib.auth import get_user_model


class TeamMemberSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=get_user_model().objects.all(),
        slug_field="username",
    )

    class Meta:
        model = TeamMember
        fields = ["id", "user", "is_admin"]
        extra_kwargs = {"is_admin": {"read_only": True}}


class TeamListSerializer(serializers.Serializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True, view_name="team:team-detail"
    )
    name = serializers.CharField()


class TeamSerializer(serializers.ModelSerializer):
    # members_list = serializers.HyperlinkedRelatedField(
    #     view_name="team:member-list", read_only=True
    # )

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "description",
            "public_edit",
            "privacy_edit",
            # "members_list",
        ]

    def to_representation(self, instance):
        """Remove public_edit and privacy_edit fields for regular members"""
        ret = super().to_representation(instance)
        user = self.context["request"].user
        team_member = instance.member.get(user=user)
        if team_member.is_admin == False:
            ret.pop("public_edit", None)
            ret.pop("privacy_edit", None)
        return ret

    def create(self, validated_data):
        # member_list = validated_data.pop("member", None)
        validated_data.pop("public_edit", None)
        validated_data.pop("privacy_edit", None)

        team = Team.objects.create(**validated_data)
        user = self.context["request"].user
        TeamMember.objects.create(user=user, team=team, is_admin=True)
        return team

    def check_user_is_admin(self, user, team):
        member = team.member.get(user=user)
        if member.is_admin:
            return True
        return False

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not self.check_user_is_admin(user, instance):
            if (
                "public_edit" in validated_data.keys()
                or "privacy_edit" in validated_data.keys()
            ):
                raise serializers.ValidationError(
                    "Only team admins are allowed to change these settings",
                )

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
