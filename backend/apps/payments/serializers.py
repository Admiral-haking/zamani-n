from rest_framework import serializers

import os

from apps.payments.models import Payment



class PaymentSerializer(serializers.ModelSerializer):


    receipt_name = serializers.SerializerMethodField()


    class Meta:

        model = Payment


        fields = "__all__"


        read_only_fields = (

            "status",

            "finance_processed",

            "created_at",

        )


    def get_receipt_name(self, obj):

        if not obj.receipt:

            return ""

        return os.path.basename(obj.receipt.name)



    def validate_amount(self, value):


        if value <= 0:

            raise serializers.ValidationError(

                "Amount must be greater than zero."

            )


        return value


    def validate_order(self, order):

        user = self.context["request"].user


        if (

            user.role == "CUSTOMER"

            and order.customer.user_id != user.id

        ):

            raise serializers.ValidationError(

                "شما فقط می‌توانید برای سفارش‌های خودتان پرداخت ثبت کنید."

            )


        return order