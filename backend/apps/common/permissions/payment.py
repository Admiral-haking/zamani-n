from rest_framework.permissions import BasePermission



class CanManagePayment(BasePermission):


    def has_permission(self, request, view):

        user = request.user


        if not user.is_authenticated:

            return False



        return user.role in [

            "ADMIN",

            "SECRETARY",

            "CUSTOMER"

        ]


    def has_object_permission(self, request, view, obj):

        user = request.user


        if user.role in ["ADMIN", "SECRETARY"] or user.is_superuser:

            return True


        # مشتری فقط به پرداخت‌های سفارش‌های خودش دسترسی دارد

        return obj.order.customer.user_id == user.id