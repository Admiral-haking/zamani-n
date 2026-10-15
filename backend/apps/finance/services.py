from django.db import transaction

from django.db.models import F


from apps.customers.models import Customer


from .models import Transaction




class FinanceService:
    """
    Central service for customer financial operations.
    """



    @staticmethod
    @transaction.atomic
    def add_debt(
        customer: Customer,
        amount,
        description="",
        order=None,
    ):

        """
        Increase customer debt after purchase.
        """



        # افزایش اتمیک سمت دیتابیس تا آپدیت‌های همزمان گم نشوند

        Customer.objects.filter(
            pk=customer.pk
        ).update(
            account_balance=F("account_balance") + amount
        )

        customer.refresh_from_db(
            fields=["account_balance"]
        )



        Transaction.objects.create(


            user=customer.user,


            customer=customer,


            amount=amount,


            transaction_type=Transaction.Type.ORDER_DEBT,


            description=description,


            order=order,


        )



        return customer



    @staticmethod
    @transaction.atomic
    def add_payment(
        customer: Customer,
        amount,
        description="",
        payment=None
    ):

        """
        Register customer payment.
        """



        # کاهش اتمیک سمت دیتابیس تا آپدیت‌های همزمان گم نشوند

        Customer.objects.filter(
            pk=customer.pk
        ).update(
            account_balance=F("account_balance") - amount
        )

        customer.refresh_from_db(
            fields=["account_balance"]
        )



        Transaction.objects.create(


            user=customer.user,


            customer=customer,


            amount=amount,


            transaction_type=Transaction.Type.PAYMENT,


            description=description,


            payment=payment


        )



        return customer



    @staticmethod
    def get_balance(customer: Customer):
        return customer.account_balance