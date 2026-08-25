from django.db import models
import uuid  # 👈 برای تولید کد رهگیری

from apps.customers.models import Customer
from apps.products.models import Product


class Order(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("PREPARING", "Preparing"),
        ("SHIPPED", "Shipped"),        # 👈 اضافه شد
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ========================================
    # 👇 فیلد جدید: کد رهگیری
    # ========================================
    tracking_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="کد رهگیری"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Order #{self.id}"

    # ========================================
    # 👇 تابع تولید کد رهگیری
    # ========================================
    def generate_tracking_code(self):
        """تولید کد رهگیری یکتا"""
        if not self.tracking_code:
            random_part = str(uuid.uuid4())[:6].upper()
            self.tracking_code = f"TRK-{self.id}-{random_part}"
            self.save(update_fields=['tracking_code'])
        return self.tracking_code


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_items"
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product.name}"