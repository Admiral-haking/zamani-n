from django.conf import settings
from django.db import models

from apps.customers.models import Customer


class SmsMessage(models.Model):
    """ثبت پیامک‌های ارسالی به مشتریان (درگاه ارسال پس از اتصال در provider پیاده می‌شود)"""

    class Status(models.TextChoices):
        LOGGED = 'logged', 'ثبت شد'
        SENT = 'sent', 'ارسال شد'
        FAILED = 'failed', 'ناموفق'

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_messages',
        verbose_name='مشتری',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_sms',
        verbose_name='فرستنده',
    )

    phone = models.CharField(max_length=20, verbose_name='شماره مقصد')
    subject = models.CharField(max_length=200, blank=True, default='', verbose_name='موضوع')
    body = models.TextField(verbose_name='متن پیامک')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.LOGGED,
        verbose_name='وضعیت',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'پیامک'
        verbose_name_plural = 'پیامک‌ها'

    def __str__(self):
        return f'{self.phone} - {self.created_at:%Y-%m-%d}'
