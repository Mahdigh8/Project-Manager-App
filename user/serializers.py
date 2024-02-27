from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, password_validation
from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from rest_framework import serializers


class CreateUserSerializer(serializers.ModelSerializer):
    """Serializer for creating new user"""

    class Meta:
        model = get_user_model()
        fields = ["username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        """Checks password validation"""
        # the below function will check for password length, commonly and only numeric
        # it will raise ValidationError on error
        password_validation.validate_password(value)

        return value

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


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """

    email = serializers.EmailField()

    reset_form = None

    def validate_email(self, value):
        # Create PasswordResetForm with the serializer initial data
        self.reset_form = PasswordResetForm(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        return value

    def save(self):
        request = self.context.get("request")
        # Set some values to trigger the send_email method.
        opts = {
            "use_https": request.is_secure(),
            "from_email": getattr(settings, "DEFAULT_FROM_EMAIL"),
            "request": request,
            "token_generator": default_token_generator,
            "subject_template_name": "users/password_reset_subject.txt",
            "email_template_name": "users/password_reset_email.html",
        }

        self.reset_form.save(**opts)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset attempt.
    """

    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)
    uid = serializers.CharField()
    token = serializers.CharField()

    user = None
    set_password_form = None

    def validate(self, attrs):
        # Decode the uidb64 (allauth use base36) to uid to get User object
        try:
            uid = force_str(uid_decoder(attrs["uid"]))
            self.user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            raise serializers.ValidationError({"uid": [_("Invalid value")]})

        if not default_token_generator.check_token(self.user, attrs["token"]):
            raise serializers.ValidationError({"token": [_("Invalid value")]})

        # Construct SetPasswordForm instance
        self.set_password_form = SetPasswordForm(
            user=self.user,
            data=attrs,
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        return self.set_password_form.save()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get("request")
        self.user = getattr(self.request, "user", None)

    def validate_old_password(self, value):
        invalid_password_conditions = (
            self.user,
            not self.user.check_password(value),
        )

        if all(invalid_password_conditions):
            err_msg = _(
                "Your old password was entered incorrectly. Please enter it again."
            )
            raise serializers.ValidationError(err_msg)
        return value

    def validate(self, attrs):
        self.set_password_form = SetPasswordForm(
            user=self.user,
            data=attrs,
        )

        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()
