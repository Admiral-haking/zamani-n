from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    فقط کاربرانی که نقش ADMIN دارند می‌توانند به پنل صاحب شرکت دسترسی داشته باشند
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    فقط ADMIN می‌تواند تغییرات اعمال کند، بقیه فقط می‌توانند بخوانند
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == 'ADMIN'