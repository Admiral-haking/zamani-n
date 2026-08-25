from rest_framework import serializers

from .models import Customer



class DistributorCustomerSerializer(serializers.ModelSerializer):


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

            "created_at",

            "updated_at",

        )


        read_only_fields = (

            "id",

            "account_balance",

            "created_at",

            "updated_at",

        )