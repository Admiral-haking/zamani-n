from django.db import models
from apps.accounts.models import User


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "باز"
        ANSWERED = "ANSWERED", "پاسخ داده شده"
        CLOSED = "CLOSED", "بسته شده"

    class Category(models.TextChoices):
        GENERAL = "GENERAL", "عمومی"
        ORDER = "ORDER", "مشکل سفارش"
        PRODUCT = "PRODUCT", "سوال درباره محصول"
        DELIVERY = "DELIVERY", "مشکل ارسال"
        PAYMENT = "PAYMENT", "مشکل پرداخت"
        TECHNICAL = "TECHNICAL", "مشکل فنی"
        SUGGESTION = "SUGGESTION", "پیشنهاد"
        COMPLAINT = "COMPLAINT", "شکایت"
        ACCOUNT_REQUEST = "ACCOUNT_REQUEST", "درخواست ایجاد حساب"

    class Priority(models.TextChoices):
        LOW = "LOW", "کم"
        MEDIUM = "MEDIUM", "متوسط"
        HIGH = "HIGH", "بالا"

    # برای تیکت‌های مهمان (درخواست حساب) خالی است
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=True,
        blank=True,
    )

    guest_name = models.CharField(max_length=150, blank=True, default="")
    guest_phone = models.CharField(max_length=15, blank=True, default="")

    title = models.CharField(max_length=200)
    message = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    admin_reply = models.TextField(blank=True, null=True)
    admin_replied_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tickets"
        ordering = ["-created_at"]

    def __str__(self):
        owner = self.user.username if self.user else (self.guest_name or "مهمان")
        return f"{self.title} - {owner}"

    def mark_as_answered(self, reply_message):
        self.admin_reply = reply_message
        self.admin_replied_at = models.DateTimeField(auto_now=True)
        self.status = self.Status.ANSWERED
        self.save()