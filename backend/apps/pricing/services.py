from apps.distributors.models import Distributor
from apps.products.models import Product

from .models import DistributorPrice, ProductPrice


class PricingSelector:
    """کوئری‌های قیمت‌گذاری"""

    @staticmethod
    def distributor_shop(distributor):
        """قیمت‌های فروشگاه یک پخش‌کننده"""
        return DistributorPrice.objects.filter(
            distributor=distributor
        ).select_related("product", "distributor")

    @staticmethod
    def all_prices():
        return DistributorPrice.objects.select_related(
            "product", "distributor"
        ).all()

    # ---------- سازگاری با کد قدیمی (per-customer، منسوخ) ----------

    @staticmethod
    def customer_prices(customer):
        return ProductPrice.objects.filter(
            customer=customer
        ).select_related(
            "product",
            "customer"
        )


def get_product_price(customer, product: Product):
    """
    قیمت مؤثر محصول برای مشتری (اولویت‌دار):

    1. قیمت دستی ثبت‌شده برای همین مشتری (پخش‌کننده در پنل ست کرده)
    2. قیمت فروشگاه پخش‌کننده معرف مشتری
    3. قیمت پایه شرکت (fallback مصوب کارفرما)
    """

    custom_price = (
        ProductPrice.objects
        .filter(customer=customer, product=product)
        .values_list("price", flat=True)
        .first()
    )

    if custom_price is not None:

        return custom_price

    distributor = getattr(customer, "distributor", None)

    if distributor is not None:

        shop_price = (
            DistributorPrice.objects
            .filter(distributor=distributor, product=product)
            .values_list("price", flat=True)
            .first()
        )

        if shop_price is not None:

            return shop_price

    return product.base_price
