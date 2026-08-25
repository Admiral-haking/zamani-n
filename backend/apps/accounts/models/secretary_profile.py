from django.db import models
from .user import User


class SecretaryProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="secretary_profile"
    )


    employee_code = models.CharField(
        max_length=50,
        unique=True
    )


    phone = models.CharField(
        max_length=11,
        blank=True,
        null=True
    )


    is_active = models.BooleanField(
        default=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta:
        db_table = "secretary_profiles"


    def __str__(self):
        return self.employee_code