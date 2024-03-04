from rest_framework import permissions


class IsAllowedToUpdateOrDelete(permissions.BasePermission):
    """
    Object-level permission to only allow
    team admins to update or delete project
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        try:
            member = obj.team.member.get(user=request.user)
        except:
            return False

        if member.is_admin:
            return True

        return False
