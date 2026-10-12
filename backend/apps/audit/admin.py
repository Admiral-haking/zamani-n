from django.contrib import admin

from .models import AuditLog



@admin.register(AuditLog)

class AuditLogAdmin(admin.ModelAdmin):


    list_display = (

        "user",

        "action",

        "model_name",

        "object_id",

        "created_at",

    )


    list_filter = (

        "action",

        "model_name",

    )


    search_fields = (

        "description",

        "model_name",

    )