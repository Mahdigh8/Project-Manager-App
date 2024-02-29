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


# class IsAllowedToInviteMembers(permissions.BasePermission):
#     """
#     Object-level permission to only allow inviting members to team
#     if the user is team admin or privacy_edit is set to ALL.
#     """

#     def has_object_permission(self, request, view, obj):
#         if request.method not in ["PATCH", "PUT"]:
#             return True

#         member = obj.member.get(user=request.user)
#         if member.is_admin:
#             return True
#         elif obj.public_edit == "ALL":
#             return True

#         return False
