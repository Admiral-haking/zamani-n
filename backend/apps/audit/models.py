from django.db import models

from django.conf import settings


class AuditLog(models.Model):


    class Action(models.TextChoices):

        CREATE = "CREATE", "Create"

        UPDATE = "UPDATE", "Update"

        DELETE = "DELETE", "Delete"

        LOGIN = "LOGIN", "Login"

        PAYMENT = "PAYMENT", "Payment"

        ORDER = "ORDER", "Order"



    user = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="audit_logs"

    )


    action = models.CharField(

        max_length=20,

        choices=Action.choices

    )


    model_name = models.CharField(

        max_length=100

    )


    object_id = models.PositiveIntegerField(

        null=True,

        blank=True

    )


    description = models.TextField(

        blank=True

    )


    ip_address = models.GenericIPAddressField(

        null=True,

        blank=True

    )


    created_at = models.DateTimeField(

        auto_now_add=True

    )



    class Meta:

        db_table = "audit_logs"

        ordering = [

            "-created_at"

        ]



    def __str__(self):

        return f"{self.user} - {self.action}"