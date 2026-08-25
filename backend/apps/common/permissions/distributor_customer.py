from rest_framework.permissions import BasePermission


class IsDistributorCustomerOwner(BasePermission):

    """
    Distributor فقط به مشتری‌های خودش دسترسی دارد.
    """

    def has_object_permission(self, request, view, obj):

        user = request.user

        # ادمین و منشی
        if user.role in [
            "ADMIN",
            "SECRETARY"
        ]:
            return True

        # خود Distributor
        if user.role == "DISTRIBUTOR":

            return (
                obj.distributor is not None and
                obj.distributor.user == user
            )

        return False