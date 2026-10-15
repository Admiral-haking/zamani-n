from rest_framework import serializers

from .models import Category, Product




class CategorySerializer(serializers.ModelSerializer):


    class Meta:

        model = Category

        fields = [

            "id",

            "name",

            "is_active",

            "created_at",

        ]



        read_only_fields = [

            "created_at",

        ]





class ProductSerializer(serializers.ModelSerializer):


    category_name = serializers.CharField(

        source="category.name",

        read_only=True

    )



    class Meta:


        model = Product


        fields = [

            "id",

            "category",

            "category_name",

            "code",

            "name",

            "weight",

            "meat_percent",

            "base_price",

            "image",

            "is_active",

            "created_at",

            "updated_at",

        ]



        read_only_fields = [

            "created_at",

            "updated_at",

        ]




    def validate_weight(self, value):


        if value <= 0:

            raise serializers.ValidationError(

                "Weight must be greater than zero."

            )


        return value




    def validate_meat_percent(self, value):


        if value < 0 or value > 100:


            raise serializers.ValidationError(

                "Meat percent must be between 0 and 100."

            )


        return value




    def validate_base_price(self, value):


        if value <= 0:


            raise serializers.ValidationError(

                "Price must be greater than zero."

            )


        return value