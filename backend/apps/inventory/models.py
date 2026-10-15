from django.conf import settings
from django.db import models

from apps.products.models import Product


class InventoryLog(models.Model):

    CATEGORY_CHOICES = [
        ("90", "همبرگر ۹۰٪"),
        ("60", "همبرگر ۶۰٪"),
        ("steak", "استیک"),
        ("roast", "رست بیف"),
    ]

    UNIT_CHOICES = [
        ("package", "بسته"),
        ("carton", "کارتن"),
    ]

    DIRECTION_CHOICES = [
        ("+", "ورود"),
        ("-", "خروج"),
    ]

    product = models.CharField(
        max_length=150
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="90"
    )

    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default="package"
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    direction = models.CharField(
        max_length=4,
        choices=DIRECTION_CHOICES,
        default="+"
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_logs",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "inventory_log"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.product} {self.get_direction_display()} {self.quantity}"


class Inventory(models.Model):

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory"
    )

    quantity = models.PositiveIntegerField(
        default=0
    )

    minimum_stock = models.PositiveIntegerField(
        default=10
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock

    class Meta:
        db_table = "inventory"

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"