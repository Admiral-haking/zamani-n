from django.conf import settings
from django.db import models


class Category(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=200
    )

    weight = models.PositiveIntegerField()

    meat_percent = models.PositiveIntegerField()

    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    # ========================================
    # 👇 فیلدهای جدید برای پرفروش‌ها
    # ========================================
    is_featured = models.BooleanField(
        default=False,
        verbose_name="ویژه (پیشنهاد شگفت‌انگیز)"
    )

    discount_percent = models.PositiveIntegerField(
        default=0,
        verbose_name="درصد تخفیف",
        help_text="عدد بین 0 تا 100"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "products"
        ordering = ["name"]

    def can_delete(self):
        return not self.orderitem_set.exists()

    # ========================================
    # 👇 متد محاسبه قیمت با تخفیف
    # ========================================
    def get_discounted_price(self):
        """محاسبه قیمت پس از اعمال تخفیف"""
        if self.discount_percent > 0:
            return self.base_price * (1 - self.discount_percent / 100)
        return self.base_price

    def __str__(self):
        return self.name


class ProductDiscount(models.Model):
    """تخفیف محصولی که منشی در پنل مدیریت ثبت می‌کند (کد + درصد + بازه)"""

    product_name = models.CharField(
        max_length=200,
        verbose_name="نام محصول",
    )

    percent = models.PositiveIntegerField(
        verbose_name="درصد تخفیف",
        help_text="عدد بین 1 تا 100"
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد تخفیف",
    )

    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ شروع",
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ انقضا",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_discounts",
        verbose_name="ثبت‌کننده",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "products_discount"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product_name} {self.percent}%"