from django.contrib import admin
from .models import CustomUser, Team, TeamMember, Project, Task, Comment

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Comment)
