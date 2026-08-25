from django.db import models
from django.conf import settings


class Distributor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="distributor_profile"
    )

    distributor_code = models.CharField(
        max_length=20,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=11,
        unique=True
    )

    # ================ فیلد جدید ================
    city = models.CharField(
        max_length=100,
        default="تهران"
    )
    # ============================================

    address = models.TextField(
        blank=True
    )

    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
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
        db_table = "distributors"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.distributor_code:
            import random
            import string
            self.distributor_code = 'DIS-' + ''.join(
                random.choices(string.digits, k=8)
            )
        super().save(*args, **kwargs)