from django.db import models
from apps.customers.models import Customer
from apps.orders.models import Order, OrderItem


class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار بررسی'),
        ('APPROVED', 'تایید شده'),
        ('REJECTED', 'رد شده'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELLED', 'لغو شده'),
    ]
    
    REASON_CHOICES = [
        ('DEFECTIVE', 'محصول معیوب است'),
        ('WRONG', 'محصول اشتباه ارسال شده'),
        ('DAMAGED', 'آسیب دیده در حمل و نقل'),
        ('EXPIRED', 'تاریخ انقضا گذشته'),
        ('OTHER', 'سایر موارد'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='return_requests'
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='return_requests'
    )
    
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='return_requests',
        null=True,
        blank=True
    )
    
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    image = models.ImageField(upload_to='returns/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Return #{self.id} - {self.customer.company_name}"