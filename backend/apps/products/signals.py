from django.db.models.signals import post_save
from django.dispatch import receiver


from apps.products.models import Product
from apps.inventory.models import Inventory



@receiver(
    post_save,
    sender=Product
)
def create_product_inventory(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        Inventory.objects.get_or_create(

            product=instance,

            defaults={

                "quantity": 0,

                "minimum_stock": 10

            }

        )