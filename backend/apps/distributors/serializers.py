from rest_framework import serializers

from .models import Distributor


class DistributorSerializer(serializers.ModelSerializer):


    customer_count = serializers.SerializerMethodField()


    class Meta:

        model = Distributor

        fields = [
            "id",
            "distributor_code",
            "full_name",
            "phone",
            "address",
            "commission_percent",
            "is_active",
            "customer_count",
        ]


    def get_customer_count(self,obj):

        return obj.customers.count()