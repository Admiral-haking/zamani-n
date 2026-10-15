from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """
    Allow access only to authenticated active users.
    """

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.is_active
        )