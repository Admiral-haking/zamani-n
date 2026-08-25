from .models import ProductPrice




class PricingService:


    @staticmethod
    def get_customer_price(
        customer,
        product
    ):


        price = ProductPrice.objects.filter(

            customer=customer,

            product=product

        ).first()



        if not price:

            return None



        return price.price




    @staticmethod
    def set_customer_price(

        customer,

        product,

        price

    ):


        product_price, _ = ProductPrice.objects.update_or_create(


            customer=customer,


            product=product,


            defaults={

                "price": price

            }

        )


        return product_price




    @staticmethod
    def delete_customer_price(

        customer,

        product

    ):


        return ProductPrice.objects.filter(

            customer=customer,

            product=product

        ).delete()




def get_product_price(

    customer,

    product

):


    price = PricingService.get_customer_price(

        customer,

        product

    )

    if price is None:


        # در نبود قیمت اختصاصی، قیمت پایه محصول ملاک است

        return product.base_price



    return price