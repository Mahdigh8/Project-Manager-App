from django.urls import path
from . import views


app_name = "user"

urlpatterns = [
    path("register/", views.CreateUserView.as_view(), name="register"),
    path("token/", views.CreateTokenView.as_view(), name="token"),
    path("profile/", views.ManageUserView.as_view(), name="profile"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "password/change/", views.PasswordChangeView.as_view(), name="password-change"
    ),
]
