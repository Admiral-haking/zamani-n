from rest_framework.permissions import BasePermission


class IsAdminOrSecretary(BasePermission):

    def has_permission(self, request, view):

        # همه کاربران لاگین کرده بتوانند مشاهده کنند
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # فقط ادمین و منشی بتوانند ایجاد، ویرایش و حذف کنند
        return (
            request.user.is_superuser or
            request.user.role in ["ADMIN", "SECRETARY"]
        )