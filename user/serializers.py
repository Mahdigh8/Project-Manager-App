from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class CreateUserSerializer(serializers.ModelSerializer):
    """Serializer for creating new user"""

    class Meta:
        model = get_user_model()
        fields = ["username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for retrieve and update user instances"""

    class Meta:
        model = get_user_model()
        fields = ["username", "email", "first_name", "last_name", "date_joined"]
        extra_kwargs = {
            "email": {"read_only": True},
            "date_joined": {"read_only": True},
        }


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user authentication object"""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=True
    )

    def validate(self, attrs):
        email = attrs.get("email", None)
        password = attrs.get("password", None)

        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )
        if user is None:
            msg = _("Unable to authenticate with provided credentials")
            raise serializers.ValidationError(msg, code="authentication")

        attrs["user"] = user
        return attrs
