from django.db import models
from apps.accounts.models import User


class TicketMessage(models.Model):
    class Sender(models.TextChoices):
        CUSTOMER = "CUSTOMER", "مشتری"
        STAFF = "STAFF", "پرسنل"
        GUEST = "GUEST", "مهمان"

    ticket = models.ForeignKey(
        "Ticket",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.CharField(
        max_length=20,
        choices=Sender.choices,
        default=Sender.CUSTOMER,
    )
    sender_name = models.CharField(max_length=150, blank=True, default="")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tickets_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"Ticket#{self.ticket_id} - {self.sender}: {self.text[:50]}"


class TicketAttachment(models.Model):
    message = models.ForeignKey(
        TicketMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(
        upload_to="ticket_messages/%Y/%m/",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tickets_attachments"
        ordering = ["created_at"]

    def __str__(self):
        return f"TicketMessage#{self.message_id} - {self.file.name}"


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
    guest_email = models.EmailField(max_length=254, blank=True, default="")
    guest_key = models.CharField(max_length=120, blank=True, default="", db_index=True)

    title = models.CharField(max_length=200)
    message = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    admin_reply = models.TextField(blank=True, null=True)
    admin_replied_at = models.DateTimeField(blank=True, null=True)

    # پیام اضافه از طرف مشتری (چند چرخه پاسخ بین مشتری و منشی)
    customer_reply = models.TextField(blank=True, null=True)
    customer_replied_at = models.DateTimeField(blank=True, null=True)

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
