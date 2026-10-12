from django.db import models

from apps.products.models import Product
from apps.customers.models import Customer


class ProductPrice(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="customer_prices"
    )


    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="prices"
    )


    price = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta:

        db_table = "product_prices"

        ordering = [
            "customer",
            "product"
        ]


        constraints = [

            models.UniqueConstraint(
                fields=[
                    "customer",
                    "product"
                ],
                name="unique_customer_product_price"
            )

        ]


    def __str__(self):

        return (
            f"{self.customer.customer_code} - "
            f"{self.product.name}"
        )


class DistributorPrice(models.Model):
    """
    قیمت فروشگاهِ هر پخش‌کننده.

    منشی/ادمین محصول را با قیمت پایه ثبت می‌کنند و هر پخش‌کننده
    برای پنل خودش روی همان محصول قیمتی دلخواه تعیین می‌کند.
    """

    distributor = models.ForeignKey(
        "distributors.Distributor",
        on_delete=models.CASCADE,
        related_name="shop_prices",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="distributor_prices",
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "distributor_prices"
        ordering = ["distributor", "product"]
        constraints = [
            models.UniqueConstraint(
                fields=["distributor", "product"],
                name="unique_distributor_product_price",
            ),
        ]

    def __str__(self):
        return f"{self.distributor} - {self.product.name}: {self.price}"