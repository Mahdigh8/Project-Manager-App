from django.urls import path, include
from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter()
router.register("", views.TeamViewSet)

app_name = "team"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "<int:pk>/remove/<int:member_id>/",
        views.TeamViewSet.as_view({"delete": "remove_member"}),
        name="remove-member",
    ),
]
