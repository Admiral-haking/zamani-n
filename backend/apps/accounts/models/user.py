from django.db import models
from django.contrib.auth.models import AbstractUser


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
        unique=True,
        blank=True,
        null=True
    )


    national_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True
    )


    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )


    mobile_verified = models.BooleanField(
        default=False
    )


    email_verified = models.BooleanField(
        default=False
    )


    is_deleted = models.BooleanField(
        default=False
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