from django.conf import settings
from django.db import models

from apps.customers.models import Customer


class Reminder(models.Model):
    """یادآوری پیگیری مشتری (ساخته منشی یا پخش‌کننده)"""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name='مشتری',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_reminders',
        verbose_name='ثبت‌کننده',
    )

    title = models.CharField(max_length=200, verbose_name='عنوان')
    message = models.TextField(blank=True, default='', verbose_name='متن یادآوری')
    remind_at = models.DateTimeField(verbose_name='زمان یادآوری')
    is_done = models.BooleanField(default=False, verbose_name='انجام شده')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['is_done', 'remind_at']
        verbose_name = 'یادآوری'
        verbose_name_plural = 'یادآوری‌ها'

    def __str__(self):
        return f'{self.title} - {self.customer_id}'
