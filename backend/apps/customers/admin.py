from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "customer_code",
        "company_name",
        "phone",
        "account_balance",
        "is_active",
        "created_at",
    ]


    search_fields = [
        "customer_code",
        "company_name",
        "phone",
        "user__username",
    ]


    list_filter = [
        "is_active",
        "created_at",
    ]