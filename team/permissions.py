from rest_framework import permissions


class IsAllowedToEdit(permissions.BasePermission):
    """
    Object-level permission to only allow edit in team settings
    if the user is team admin or public_edit is set to ALL.
    """

    def has_object_permission(self, request, view, obj):
        if request.method not in ["PATCH", "PUT"]:
            return True

        member = obj.member.get(user=request.user)
        if member.is_admin:
            return True
        elif obj.public_edit == "ALL":
            return True

        return False


class IsAllowedToDelete(permissions.BasePermission):
    """
    Object-level permission to only allow team admins to delete team
    """

    def has_object_permission(self, request, view, obj):
        if request.method != "DELETE":
            return True

        member = obj.member.get(user=request.user)
        if member.is_admin:
            return True

        return False


class IsAllowedToAddOrEditMembers(permissions.BasePermission):
    """
    Object-level permission to only allow
    team admins to add or update members
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        member = obj.member.get(user=request.user)
        if member.is_admin:
            return True

        return False


class IsAllowedToRemoveMembers(permissions.BasePermission):
    """
    Object-level permission to only allow team admins
    to remove other members or the user to leave the group
    """

    def has_object_permission(self, request, view, obj, **kwargs):
        if request.method in permissions.SAFE_METHODS:
            return True

        team = kwargs.get("team", None)
        if not team:
            return False

        member = team.member.get(user=request.user)
        if member.is_admin:
            return True

        return obj.user.id == request.user.id
