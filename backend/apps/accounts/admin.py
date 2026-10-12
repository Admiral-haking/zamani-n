from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "first_name",
        "last_name",
        "phone",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "phone",
        "first_name",
        "last_name",
    )

    list_filter = (
        "is_staff",
        "is_active",
        "groups",
    )