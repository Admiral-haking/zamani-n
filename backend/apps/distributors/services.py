from django.db.models import Sum

from apps.customers.models import Customer
from apps.orders.models import Order


class DistributorService:


    @staticmethod
    def get_customers(distributor):

        return Customer.objects.filter(
            distributor=distributor
        )


    @staticmethod
    def get_orders(distributor):

        return Order.objects.filter(
            customer__distributor=distributor
        )


    @staticmethod
    def customer_count(distributor):

        return DistributorService.get_customers(
            distributor
        ).count()



    @staticmethod
    def order_count(distributor):

        return DistributorService.get_orders(
            distributor
        ).count()



    @staticmethod
    def total_sales(distributor):

        result = (
            DistributorService
            .get_orders(distributor)
            .aggregate(
                total=Sum("total_price")
            )
        )

        return result["total"] or 0