from django.contrib import admin

from .models import SmsMessage


@admin.register(SmsMessage)
class SmsMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'customer', 'sender', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('phone', 'body', 'customer__company_name')
