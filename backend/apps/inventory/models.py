from django.db import models

from apps.products.models import Product


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