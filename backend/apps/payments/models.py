from django.db import models

from apps.orders.models import Order



class Payment(models.Model):


    class Method(models.TextChoices):

        CASH = "CASH", "Cash"

        CARD = "CARD", "Card To Card"

        ONLINE = "ONLINE", "Online"

        BALANCE = "BALANCE", "Account Balance"

        CHECK = "CHECK", "Check"



    class Status(models.TextChoices):

        PENDING = "PENDING", "Pending"

        SUCCESS = "SUCCESS", "Success"

        FAILED = "FAILED", "Failed"



    order = models.ForeignKey(

        Order,

        on_delete=models.CASCADE,

        related_name="payments"

    )



    amount = models.DecimalField(

        max_digits=12,

        decimal_places=0

    )



    method = models.CharField(

        max_length=20,

        choices=Method.choices

    )



    status = models.CharField(

        max_length=20,

        choices=Status.choices,

        default=Status.PENDING

    )



    finance_processed = models.BooleanField(

        default=False

    )



    reference_number = models.CharField(

        max_length=100,

        blank=True

    )



    created_at = models.DateTimeField(

        auto_now_add=True

    )



    class Meta:

        db_table = "payments"



    def __str__(self):

        return f"Payment {self.id}"