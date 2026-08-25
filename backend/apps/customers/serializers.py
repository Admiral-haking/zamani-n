from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Customer



User = get_user_model()




class CustomerSerializer(serializers.ModelSerializer):


    username = serializers.CharField(
        write_only=True
    )


    password = serializers.CharField(
        write_only=True
    )



    role = serializers.CharField(

        source="user.role",

        read_only=True

    )



    class Meta:


        model = Customer


        fields = (

            "id",

            "username",

            "password",

            "customer_code",

            "company_name",

            "phone",

            "address",

            "account_balance",

            "is_active",

            "role",

            "created_at",

            "updated_at",

        )



        read_only_fields = (

            "created_at",

            "updated_at",

            "account_balance",

            "role",

        )





    def validate_username(

        self,

        value

    ):


        if User.objects.filter(

            username=value

        ).exists():


            raise serializers.ValidationError(

                "Username already exists."

            )


        return value




    def validate_phone(

        self,

        value

    ):


        if User.objects.filter(

            phone=value

        ).exists():


            raise serializers.ValidationError(

                "Phone already exists."

            )


        return value




    def create(

        self,

        validated_data

    ):


        username = validated_data.pop(

            "username"

        )


        password = validated_data.pop(

            "password"

        )



        user = User.objects.create(

            username=username,

            role=User.Role.CUSTOMER,

            phone=validated_data.get("phone")

        )



        user.set_password(

            password

        )


        user.save()



        customer = Customer.objects.create(

            user=user,

            **validated_data

        )



        return customer






class DistributorCustomerSerializer(

    serializers.ModelSerializer

):


    class Meta:


        model = Customer


        fields = (

            "id",

            "customer_code",

            "company_name",

            "phone",

            "address",

            "account_balance",

            "is_active",

        )



        read_only_fields = (

            "account_balance",

        )