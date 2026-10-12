from rest_framework.permissions import BasePermission



class CanManageInventory(BasePermission):


    def has_permission(self, request, view):


        if not request.user.is_authenticated:

            return False



        return request.user.role in [

            "ADMIN",

            "SECRETARY"

        ]