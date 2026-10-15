from rest_framework.permissions import BasePermission


class IsAdminOrSecretary(BasePermission):

    def has_permission(self, request, view):

        # Never inspect role/superuser on AnonymousUser. Protected endpoints
        # must return a clean 401 instead of leaking a server-side 500.
        if not request.user or not request.user.is_authenticated:
            return False

        # همه کاربران لاگین کرده بتوانند مشاهده کنند
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # فقط ادمین و منشی بتوانند ایجاد، ویرایش و حذف کنند
        return (
            bool(getattr(request.user, "is_superuser", False)) or
            getattr(request.user, "role", None) in ["ADMIN", "SECRETARY"]
        )
