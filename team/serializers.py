from rest_framework import serializers
from core.models import Team, TeamMember
from django.contrib.auth import get_user_model


class TeamMemberListSerializer(serializers.ListSerializer):
    """Serializer for creating and updating multiple team members"""

    def create(self, validated_data):
        """Adding multiple member to team"""
        team = validated_data[0].pop("team", None)
        if team == None:
            raise serializers.ValidationError(
                "Team object should be specified for adding members"
            )

        team_members = []
        for item in validated_data:
            email = item.pop("user").get("email", None)
            try:
                user = get_user_model().objects.get(email=email)
                ## check for duplication of member in the team
                ## if member is not already in the team then add it.
                if not team.member.filter(user=user).exists():
                    team_members.append(
                        TeamMember(team=team, user=user, is_admin=False)
                    )
            except:
                raise serializers.ValidationError(
                    f"There is no user with email {email}"
                )

        return TeamMember.objects.bulk_create(team_members)

    def update(self, instance, validated_data):
        """Updating multiple members of the team"""
        member_mapping = {member.id: member for member in instance}
        data_mapping = {}
        for item in validated_data:
            if not item.get("id", None):
                raise serializers.ValidationError("id field is missing")
            data_mapping[item.get("id")] = item

        objs = []
        for member_id, data in data_mapping.items():
            member = member_mapping.get(member_id, None)
            if member is None:
                raise serializers.ValidationError(f"No such member with id {member_id}")
            else:
                member.is_admin = data.get("is_admin", False)
                objs.append(member)

        TeamMember.objects.bulk_update(objs, ["is_admin"])
        return objs


class TeamMemberSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        source="user.first_name", read_only=True, required=False
    )
    last_name = serializers.CharField(
        source="user.last_name", read_only=True, required=False
    )
    email = serializers.EmailField(source="user.email", required=False)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = TeamMember
        fields = ["id", "email", "last_name", "first_name", "is_admin"]
        list_serializer_class = TeamMemberListSerializer


class TeamListSerializer(serializers.Serializer):
    """Serializer for listing team objects"""

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
