from django.contrib import admin
from .models import ReturnRequest


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'order', 'product_name', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['customer__company_name', 'product_name', 'order__id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('customer', 'order', 'order_item', 'product_name', 'quantity')
        }),
        ('جزئیات مرجوعی', {
            'fields': ('reason', 'description', 'image')
        }),
        ('وضعیت', {
            'fields': ('status',)
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at')
        }),
    )