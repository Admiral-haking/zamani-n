from rest_framework import serializers

from .models import ProductPrice



class ProductPriceSerializer(serializers.ModelSerializer):


    customer_name = serializers.CharField(
        source="customer.company_name",
        read_only=True
    )


    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )



    class Meta:

        model = ProductPrice


        fields = [

            "id",

            "customer",

            "customer_name",

            "product",

            "product_name",

            "price",

            "created_at",

            "updated_at",

        ]


        read_only_fields = [

            "created_at",

            "updated_at"

        ]



    def validate_price(self,value):


        if value <= 0:

            raise serializers.ValidationError(

                "Price must be greater than zero."

            )


        return value