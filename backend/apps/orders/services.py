from django.db import connection, transaction

from django.db.models import F
import uuid  # 👈 برای تولید کد رهگیری

from apps.finance.services import FinanceService
from apps.finance.models import Transaction
from apps.customers.models import Customer
from apps.pricing.services import get_product_price
from apps.cart.models import Cart
from apps.orders.models import Order, OrderItem
from apps.inventory.models import Inventory
from apps.products.models import Product


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        customer,
        request_items=None,
        defer_debt=False,
        trust_client_prices=False,
        allow_product_creation=False,
    ):
        """
        ساخت سفارش از سبد.

        اگر اقلام معتبر در `request_items` باشد، همان چیزی که مشتری در سبد
        انتخاب و تأیید کرده است ثبت می‌شود و سبد قدیمی سرور نادیده گرفته
        می‌شود. در غیر این صورت از سبد سرور (`Cart`) خوانده می‌شود.
        موجودی هرگز مانع ثبت سفارش نمی‌شود (انبار همیشه پر).

        قیمت سفارش مشتری همیشه از منبع معتبر سمت سرور محاسبه می‌شود و قیمت
        ارسالی مرورگر نادیده گرفته می‌شود. فقط فروش دستی پرسنل/پخش‌کننده
        می‌تواند از قیمت ارسالی استفاده کند.

        با `defer_debt=True` (روش پرداخت مانده‌حساب) نه بدهی ثبت می‌شود و نه
        موجودی کسر می‌گردد؛ فاکتور به حالت «در انتظار تأیید پخش‌کننده»
        می‌ماند تا پس از تأیید، بدهی و موجودی یک‌بار و فقط یک‌بار بنشینند.
        """

        request_entries = [
            raw for raw in (request_items or [])
            if isinstance(raw, dict)
        ]
        use_request_items = len(request_entries) > 0

        cart_items = []
        if not use_request_items:
            cart_items = list(
                Cart.objects
                .select_related("product")
                .filter(customer=customer)
            )

        if not cart_items and not use_request_items:
            raise ValueError("Cart is empty.")

        order = Order.objects.create(
            customer=customer,
            status='AWAITING_APPROVAL' if defer_debt else 'PENDING'
        )

        total = 0
        aggregated = {}

        if cart_items:
            for item in cart_items:
                product = item.product
                quantity = item.quantity

                if not product.is_active:
                    raise ValueError(f"{product.name} is inactive.")

                if quantity <= 0:
                    raise ValueError("Invalid quantity.")

                price = get_product_price(customer, product)
                key = product.id
                if key in aggregated:
                    aggregated[key]["quantity"] += quantity
                else:
                    aggregated[key] = {
                        "product": product,
                        "quantity": quantity,
                        "price": price,
                    }
        else:
            for raw in request_entries:
                try:
                    quantity = int(raw.get("quantity") or 1)
                except (TypeError, ValueError):
                    quantity = 1

                if quantity <= 0:
                    raise ValueError("Invalid quantity.")

                product = OrderService._resolve_product(
                    raw,
                    allow_create=allow_product_creation,
                )

                if trust_client_prices:
                    try:
                        price = int(raw.get("price") or 0)
                    except (TypeError, ValueError):
                        price = 0
                else:
                    price = get_product_price(customer, product)

                key = product.id
                if key in aggregated:
                    aggregated[key]["quantity"] += quantity
                else:
                    aggregated[key] = {
                        "product": product,
                        "quantity": quantity,
                        "price": price,
                    }

        if not aggregated:
            raise ValueError("سبد خرید معتبر نیست.")

        # موجودی درخواست مانده‌حساب فقط هنگام تأیید نهایی کسر می‌شود تا در
        # صورت لغو، انبار به‌اشتباه خالی نماند.
        reserve_inventory = not defer_debt

        for entry in aggregated.values():
            product = entry["product"]
            quantity = entry["quantity"]
            price = entry["price"]

            if reserve_inventory:
                OrderService._adjust_inventory(product, quantity)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )

            total += price * quantity

        order.total_price = total
        order.save()

        order.generate_tracking_code()

        if cart_items:
            Cart.objects.filter(
                customer=customer
            ).delete()

        if defer_debt:
            return order

        return OrderService.record_debt(order)

    @staticmethod
    @transaction.atomic
    def record_debt(order):
        """ثبت بدهی فاکتور در حساب مشتری؛ دقیقاً یک‌بار (idempotent).

        برای فاکتورهای «مانده‌حساب» این کار تا تأیید پخش‌کننده انجام نمی‌شود.
        """

        with transaction.atomic():
            locked_order = OrderService._locked_order(order.pk)

            if locked_order.debt_recorded:
                return locked_order

            FinanceService.add_debt(
                locked_order.customer,
                int(locked_order.total_price),
                f"Order #{locked_order.id}",
                order=locked_order,
            )

            locked_order.debt_recorded = True
            locked_order.save(update_fields=["debt_recorded"])

            return locked_order

    @staticmethod
    @transaction.atomic
    def approve_balance_request(order):
        """نهایی‌سازی درخواست مانده‌حساب پس از تأیید پخش‌کننده.

        بدهی، کسر موجودی و تغییر وضعیت در یک تراکنش انجام می‌شود تا تأیید
        همزمان دو نفر هم نتواند بدهی تکراری بسازد.
        """

        locked_order = OrderService._locked_order(order.pk)

        if locked_order.status != 'AWAITING_APPROVAL':
            raise ValueError("این درخواست قبلاً بررسی شده است.")

        for item in locked_order.items.select_related("product").all():
            OrderService._adjust_inventory(item.product, item.quantity)

        if not locked_order.debt_recorded:
            FinanceService.add_debt(
                locked_order.customer,
                int(locked_order.total_price),
                f"Order #{locked_order.id}",
                order=locked_order,
            )
            locked_order.debt_recorded = True

        locked_order.status = 'CONFIRMED'
        locked_order.save(update_fields=["debt_recorded", "status"])

        return locked_order

    @staticmethod
    def _locked_order(order_id):
        """خواندن سفارش با قفل سطری، در پایگاه‌هایی که پشتیبانی می‌کنند."""

        queryset = Order.objects.select_related("customer")
        if connection.features.has_select_for_update:
            return queryset.select_for_update().get(pk=order_id)
        return queryset.get(pk=order_id)

    @staticmethod
    @transaction.atomic
    def reverse_order_finance(order):
        """برگرداندن اثر مالی یک فاکتور لغو شده از حساب مشتری.

        اگر برای این فاکتور بدهی ثبت شده باشد، مبلغ کل به‌صورت استرداد
        (RETURN) از مانده حساب مشتری کسر می‌شود تا مشتری ماندهٔ کاذب نداشته
        باشد. این عملیات فقط یک بار اجرا می‌شود (فیلد finance_reversed).
        """

        if order.finance_reversed:
            return order

        debt_txs = Transaction.objects.filter(
            customer=order.customer,
            transaction_type=Transaction.Type.ORDER_DEBT,
            description=f"Order #{order.id}"
        )

        if not debt_txs.exists():
            return order

        total = int(order.total_price)

        Customer.objects.filter(pk=order.customer_id).update(
            account_balance=F("account_balance") - total
        )

        Transaction.objects.create(
            user=order.customer.user,
            customer=order.customer,
            amount=total,
            transaction_type=Transaction.Type.RETURN,
            description=f"لغو فاکتور #{order.id}"
        )

        order.finance_reversed = True

        order.save(update_fields=["finance_reversed"])

        return order

    @staticmethod
    def _resolve_product(raw, allow_create=False):
        """یافتن محصول فعال.

        برای سفارش مشتری فقط محصول واقعی و فعال پذیرفته می‌شود تا داده
        نامعتبر نتواند وارد کاتالوگ شود. ساخت خودکار محصول فقط برای فروش
        دستی پرسنل/پخش‌کننده مجاز است.
        """

        raw_id = (
            raw.get("product")
            or raw.get("catalogId")
            or raw.get("catalog_id")
            or raw.get("id")
        )

        if raw_id is not None:
            try:
                raw_id = int(raw_id)
            except (TypeError, ValueError):
                raw_id = None
            if raw_id is not None:
                product = (
                    Product.objects
                    .filter(id=raw_id, is_active=True)
                    .first()
                )
                if product is not None:
                    return product

        name = str(raw.get("name") or "").strip()

        if name:
            product = (
                Product.objects
                .filter(name__iexact=name, is_active=True)
                .first()
            )
            if product is not None:
                return product

        if allow_create and name:
            try:
                price = int(raw.get("price") or 0)
            except (TypeError, ValueError):
                price = 0

            return Product.objects.create(
                name=name,
                code="WEB-" + str(uuid.uuid4())[:8].upper(),
                weight=0,
                meat_percent=0,
                base_price=max(price, 0),
                is_active=True,
            )

        raise ValueError("محصول انتخاب‌شده یافت نشد یا غیرفعال است.")

    @staticmethod
    def _adjust_inventory(product, quantity):
        """انبار همیشه پر؛ فقط در حد موجودی فعلی کسر می‌شود و هیچ‌وقت خطا نمی‌دهد."""

        inventory = (
            Inventory.objects
            .filter(product=product)
            .first()
        )

        if inventory is None:
            return

        if inventory.quantity < quantity:
            return

        Inventory.objects.filter(
            pk=inventory.pk,
            quantity__gte=quantity
        ).update(
            quantity=F("quantity") - quantity
        )

    # ========================================
    # 👇 تابع کمکی برای به‌روزرسانی وضعیت سفارش
    # ========================================
    @staticmethod
    @transaction.atomic
    def update_order_status(order_id, new_status):
        """به‌روزرسانی وضعیت سفارش"""
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise ValueError("Order not found")

        # وضعیت‌های معتبر
        valid_statuses = ['PENDING', 'AWAITING_APPROVAL', 'CONFIRMED', 'PREPARING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        # منطق تغییر وضعیت (اجازه نده از هر وضعیتی به هر وضعیتی بره)
        status_flow = {
            'PENDING': ['CONFIRMED', 'CANCELLED'],
            'AWAITING_APPROVAL': ['CONFIRMED', 'CANCELLED'],
            'CONFIRMED': ['PREPARING', 'CANCELLED'],
            'PREPARING': ['SHIPPED', 'CANCELLED'],
            'SHIPPED': ['DELIVERED'],
            'DELIVERED': [],
            'CANCELLED': []
        }

        if new_status not in status_flow.get(order.status, []):
            raise ValueError(f"Cannot change status from {order.status} to {new_status}")

        order.status = new_status
        order.save()

        return order

    # ========================================
    # 👇 تابع دریافت اطلاعات رهگیری
    # ========================================
    @staticmethod
    def get_order_tracking_info(order_id):
        """دریافت اطلاعات رهگیری سفارش"""
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise ValueError("Order not found")

        return {
            'order_id': order.id,
            'tracking_code': order.tracking_code or '---',
            'status': order.status,
            'created_at': order.created_at,
            'updated_at': order.updated_at
        }