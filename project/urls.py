from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProjectViewSet


router = SimpleRouter()
router.register("", ProjectViewSet, basename="project")

app_name = "project"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "<int:pk>/task/",
        ProjectViewSet.as_view({"get": "task_list", "post": "task_list"}),
        name="task-list",
    ),
    path(
        "<int:pk>/task/<int:task_id>/",
        ProjectViewSet.as_view(
            {"get": "task_detail", "patch": "task_detail", "delete": "task_detail"}
        ),
        name="task-detail",
    ),
]
