from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        SECRETARY = "SECRETARY", "Secretary"
        DISTRIBUTOR = "DISTRIBUTOR", "Distributor"
        CUSTOMER = "CUSTOMER", "Customer"


    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )


    phone = models.CharField(
        max_length=11,
        unique=True
    )


    national_code = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta:
        db_table = "users"


    def __str__(self):
        return self.username