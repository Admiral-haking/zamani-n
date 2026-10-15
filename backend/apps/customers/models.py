from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL


class Customer(models.Model):
    """مدل مشتریان"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )

    customer_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )

    company_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    shop_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="نام مغازه"
    )

    phone = models.CharField(
        max_length=15,
        unique=True
    )

    address = models.TextField(
        blank=True,
        null=True,
        default=''
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default=''
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default=''
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default=''
    )
    country = models.CharField(
        max_length=100,
        default='Iran'
    )

    account_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    economic_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    national_id = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    TAG_NORMAL = "normal"
    TAG_VIP = "vip"
    TAG_LOYAL = "loyal"
    TAG_WHOLESALE = "wholesale"
    TAG_CHOICES = [
        (TAG_NORMAL, "عادی"),
        (TAG_VIP, "VIP"),
        (TAG_LOYAL, "وفادار"),
        (TAG_WHOLESALE, "عمده‌فروش"),
    ]

    tag = models.CharField(
        max_length=20,
        choices=TAG_CHOICES,
        default=TAG_NORMAL,
        verbose_name="برچسب مشتری",
    )

    distributor = models.ForeignKey(
        'distributors.Distributor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers'
    )

    points = models.IntegerField(default=0)

    price_list = models.JSONField(
        default=dict,
        blank=True,
        help_text="قیمت‌های اختصاصی مشتری برای هر محصول (نام محصول: قیمت)"
    )

    discount_list = models.JSONField(
        default=dict,
        blank=True,
        help_text="قیمت‌های با تخفیف برای هر محصول (نام محصول: قیمت با تخفیف)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_customers'
    )

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['phone']),
            models.Index(fields=['company_name']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.customer_code or self.phone}"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def total_orders(self):
        return self.orders.filter(status='DELIVERED').count()

    @property
    def total_spent(self):
        return self.orders.filter(
            status='DELIVERED'
        ).aggregate(
            total=models.Sum('total_price')
        )['total'] or 0

    def save(self, *args, **kwargs):
        if not self.customer_code:
            import random
            import string
            self.customer_code = 'CUS-' + ''.join(
                random.choices(string.digits, k=8)
            )
        super().save(*args, **kwargs)

    def soft_delete(self):
        """حذف نرم مشتری بدون از دست رفتن سوابق سفارش و مالی"""
        self.is_active = False
        self.save(update_fields=['is_active'])


class CustomerGroup(models.Model):
    """گروه‌های مشتریان"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    customers = models.ManyToManyField(
        Customer,
        related_name='groups',
        blank=True
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_groups'
        ordering = ['name']

    def __str__(self):
        return self.name


class CustomerNote(models.Model):
    """یادداشت‌های مشتری"""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_notes'
    )
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.customer} - {self.created_at}"


class CustomerBackup(models.Model):
    """بک‌آپ کامل مشتریان: حتی اگر مشتری حذف شود، کل اطلاعات و تاریخچه‌اش می‌ماند."""

    original_customer_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="شناسه اصلی مشتری"
    )
    customer_code = models.CharField(max_length=20, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, default='')
    full_name = models.CharField(max_length=300, blank=True, default='')
    company_name = models.CharField(max_length=200, blank=True, null=True)
    shop_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, default='')
    national_id = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True, default='')
    city = models.CharField(max_length=100, blank=True, null=True, default='')
    state = models.CharField(max_length=100, blank=True, null=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, null=True, default='')
    distributor_name = models.CharField(max_length=150, blank=True, null=True)
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    is_deleted = models.BooleanField(default=False, verbose_name="حذف شده")
    deleted_at = models.DateTimeField(blank=True, null=True)

    snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="عکس کامل از اطلاعات مشتری و تمام سوابق (سفارش‌ها، پرداخت‌ها، چک‌ها، تیکت‌ها و...)"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_backups_created'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_backups_deleted'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_backups'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['is_deleted']),
            models.Index(fields=['phone']),
            models.Index(fields=['company_name']),
            models.Index(fields=['original_customer_id']),
        ]

    def __str__(self):
        return f"Backup {self.original_customer_id} - {self.company_name or self.phone}"