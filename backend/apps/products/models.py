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