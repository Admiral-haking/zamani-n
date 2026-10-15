from rest_framework.permissions import BasePermission



class IsDistributorOrAdminSecretary(BasePermission):


    def has_permission(self, request, view):

        if not request.user.is_authenticated:

            return False

        if not request.user.is_active:

            return False



        return request.user.role in [

            "ADMIN",

            "SECRETARY",

            "DISTRIBUTOR"

        ]