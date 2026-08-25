from django.contrib import admin

from .models import Distributor


@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):

    list_display = (
        "distributor_code",
        "full_name",
        "phone",
        "commission_percent",
        "is_active",
    )

    search_fields = (
        "full_name",
        "phone",
        "distributor_code",
    )

    list_filter = (
        "is_active",
    )