from django.db import models

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.common.models import BaseModel



class Transaction(BaseModel):


    class Type(models.TextChoices):

        ORDER_DEBT = "ORDER_DEBT", "Order Debt"

        PAYMENT = "PAYMENT", "Payment"

        RETURN = "RETURN", "Return"

        ADJUSTMENT = "ADJUSTMENT", "Adjustment"



    user = models.ForeignKey(

        User,

        on_delete=models.CASCADE,

        related_name="transactions"

    )



    customer = models.ForeignKey(

        Customer,

        on_delete=models.CASCADE,

        related_name="transactions",

        null=True,

        blank=True

    )



    amount = models.DecimalField(

        max_digits=12,

        decimal_places=0

    )



    transaction_type = models.CharField(

        max_length=20,

        choices=Type.choices

    )



    description = models.TextField(

        blank=True

    )



    class Meta:

        db_table = "transactions"

        ordering = [

            "-created_at"

        ]



    def __str__(self):

        return f"{self.customer.company_name} - {self.amount}"





class Check(BaseModel):


    class Status(models.TextChoices):

        PENDING = "PENDING", "Pending"

        APPROVED = "APPROVED", "Approved"

        REJECTED = "REJECTED", "Rejected"

        PAID = "PAID", "Paid"



    customer = models.ForeignKey(

        Customer,

        on_delete=models.CASCADE,

        related_name="checks"

    )



    check_number = models.CharField(

        max_length=100,

        unique=True

    )



    bank_name = models.CharField(

        max_length=100

    )



    amount = models.DecimalField(

        max_digits=12,

        decimal_places=0

    )



    issue_date = models.DateField()



    due_date = models.DateField()



    status = models.CharField(

        max_length=20,

        choices=Status.choices,

        default=Status.PENDING

    )



    image = models.ImageField(

        upload_to="checks/",

        null=True,

        blank=True

    )



    class Meta:

        db_table = "checks"

        ordering = [

            "-created_at"

        ]



    def __str__(self):

        return self.check_number