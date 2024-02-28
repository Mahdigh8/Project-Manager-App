from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    ## put username in required_fields to ask for it when creating superuser in command line.
    REQUIRED_FIELDS = ["username"]


class Team(models.Model):
    EDIT_PERMISSION_CHOICES = [
        ("ALL", "All team members"),
        ("ADMIN", "Only team admins"),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ## Who can edit the team name and description
    public_edit = models.CharField(
        max_length=10, choices=EDIT_PERMISSION_CHOICES, default="ALL"
    )
    ## Who can invite members to the team and delete the team
    privacy_edit = models.CharField(
        max_length=5, choices=EDIT_PERMISSION_CHOICES, default="ALL"
    )

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="member")
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ["user", "team"]

    def __str__(self):
        return f"{self.user.username} -> {self.team.name}"
