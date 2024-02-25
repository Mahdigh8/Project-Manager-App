from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractBaseUser):
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    ## put username in required_fields to ask for it when creating superuser in command line.
    REQUIRED_FIELDS = ["username"]
