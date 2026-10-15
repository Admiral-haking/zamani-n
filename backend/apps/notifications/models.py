from django.db import models
from apps.accounts.models import User


class Notification(models.Model):
    class Type(models.TextChoices):
        INFO = 'INFO', 'اطلاعیه'
        OFFER = 'OFFER', 'تخفیف'
        WARNING = 'WARNING', 'هشدار'
        MESSAGE = 'MESSAGE', 'پیام'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    # ========================================
    # 👇 این فیلد رو اضافه کن
    # ========================================
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INFO
    )

    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def mark_as_read(self):
        self.is_read = True
        self.save()