from django.contrib import admin

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'customer', 'created_by', 'remind_at', 'is_done', 'created_at')
    list_filter = ('is_done', 'created_at')
    search_fields = ('title', 'message', 'customer__phone', 'customer__company_name')
