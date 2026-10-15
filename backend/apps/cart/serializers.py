from rest_framework import serializers

from .models import Cart



class CartSerializer(serializers.ModelSerializer):


    product_name = serializers.CharField(

        source="product.name",

        read_only=True

    )


    customer_name = serializers.CharField(

        source="customer.company_name",

        read_only=True

    )



    class Meta:


        model = Cart


        fields = [

            "id",

            "customer",

            "customer_name",

            "product",

            "product_name",

            "quantity",

            "created_at",

        ]


        read_only_fields = [

            "customer",

            "created_at",

        ]



    def validate_quantity(self, value):


        if value <= 0:

            raise serializers.ValidationError(

                "Quantity must be greater than zero."

            )


        return value



    def validate_product(self, product):


        if not product.is_active:

            raise serializers.ValidationError(

                "Product is inactive."

            )


        return product