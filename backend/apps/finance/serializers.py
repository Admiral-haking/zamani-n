from rest_framework import serializers

from .models import Transaction, Check



class TransactionSerializer(serializers.ModelSerializer):

    class Meta:

        model = Transaction

        fields = "__all__"

        read_only_fields = (
            "created_at",
            "updated_at",
            "deleted_at",
            "is_deleted",
        )



class CheckSerializer(serializers.ModelSerializer):

    class Meta:

        model = Check

        fields = "__all__"

        read_only_fields = (
            "created_at",
            "updated_at",
            "deleted_at",
            "is_deleted",
        )