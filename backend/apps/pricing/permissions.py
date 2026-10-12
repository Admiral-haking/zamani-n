from rest_framework.permissions import BasePermission



class CanManagePrice(
    BasePermission
):


    def has_permission(
        self,
        request,
        view
    ):


        user = request.user


        if not user.is_authenticated:

            return False



        return user.role in [

            "ADMIN",

            "SECRETARY",

            "DISTRIBUTOR"

        ]