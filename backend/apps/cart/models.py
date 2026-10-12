from django.db import models

from apps.customers.models import Customer
from apps.products.models import Product



class Cart(models.Model):


    customer = models.ForeignKey(

        Customer,

        on_delete=models.CASCADE,

        related_name="cart_items"

    )


    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE,

        related_name="cart_items"

    )


    quantity = models.PositiveIntegerField(

        default=1

    )


    created_at = models.DateTimeField(

        auto_now_add=True

    )



    class Meta:

        db_table = "cart_items"


        constraints = [

            models.UniqueConstraint(

                fields=[

                    "customer",

                    "product"

                ],

                name="unique_customer_product_cart"

            )

        ]



    def __str__(self):

        return f"{self.customer} - {self.product}"