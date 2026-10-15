from rest_framework.permissions import BasePermission


class CustomerAccessPermission(BasePermission):

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):

        if request.user.is_superuser:
            return True

        if getattr(
            request.user,
            "role",
            None
        ) == "SECRETARY":
            return True

        if getattr(
            request.user,
            "role",
            None
        ) == "CUSTOMER":

            return obj.user == request.user

        return False