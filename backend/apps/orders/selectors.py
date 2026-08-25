from .models import Order



class OrderSelector:


    @staticmethod
    def all_orders():


        return Order.objects.select_related(

            "customer"

        ).prefetch_related(

            "items__product"

        )



    @staticmethod
    def customer_orders(
        customer
    ):


        return Order.objects.filter(

            customer=customer

        ).prefetch_related(

            "items__product"

        )