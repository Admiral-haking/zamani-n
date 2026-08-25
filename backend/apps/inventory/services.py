from django.db import transaction

from .models import Inventory



class InventoryService:


    @staticmethod
    @transaction.atomic
    def increase_stock(product, quantity):


        inventory, created = Inventory.objects.get_or_create(
            product=product
        )


        inventory.quantity += quantity

        inventory.save()


        return inventory




    @staticmethod
    @transaction.atomic
    def decrease_stock(product, quantity):


        inventory = (
            Inventory.objects
            .select_for_update()
            .get(product=product)
        )


        if inventory.quantity < quantity:

            raise ValueError(
                "Not enough inventory."
            )


        inventory.quantity -= quantity


        inventory.save()


        return inventory