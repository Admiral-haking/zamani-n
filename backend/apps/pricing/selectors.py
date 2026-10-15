from .models import ProductPrice



class PricingSelector:


    @staticmethod
    def customer_prices(
        customer
    ):

        return ProductPrice.objects.filter(

            customer=customer

        ).select_related(

            "product",
            "customer"

        )



    @staticmethod
    def all_prices():


        return ProductPrice.objects.select_related(

            "product",
            "customer"

        ).all()