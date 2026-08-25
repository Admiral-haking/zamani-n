from django.db import transaction

from django.db.models import F
import uuid  # 👈 برای تولید کد رهگیری

from apps.finance.services import FinanceService
from apps.pricing.services import get_product_price
from apps.cart.models import Cart
from apps.orders.models import Order, OrderItem
from apps.inventory.models import Inventory


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(customer):

        cart_items = (
            Cart.objects
            .select_related("product")
            .filter(customer=customer)
        )

        if not cart_items.exists():
            raise ValueError("Cart is empty.")

        # ========================================
        # ایجاد سفارش
        # ========================================
        order = Order.objects.create(
            customer=customer,
            status='PENDING'
        )

        total = 0

        for item in cart_items:
            product = item.product

            if not product.is_active:
                raise ValueError(f"{product.name} is inactive.")

            if item.quantity <= 0:
                raise ValueError("Invalid quantity.")

            try:
                inventory = (
                    Inventory.objects
                    .select_for_update()
                    .get(product=product)
                )
            except Inventory.DoesNotExist:
                raise ValueError(f"Inventory not found for {product.name}")

            if inventory.quantity < item.quantity:
                raise ValueError(f"Inventory of {product.name} is not enough.")

            price = get_product_price(customer, product)

            # کسر اتمیک موجودی؛ در صورت منفی شدن، تراکنش rollback می‌شود
            updated = Inventory.objects.filter(
                pk=inventory.pk,
                quantity__gte=item.quantity,
            ).update(
                quantity=F("quantity") - item.quantity
            )
            if not updated:
                raise ValueError(f"Inventory of {product.name} is not enough.")

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=price
            )

            total += price * item.quantity

        order.total_price = total
        order.save()

        # ========================================
        # 👇 تولید کد رهگیری بعد از ذخیره سفارش
        # ========================================
        order.generate_tracking_code()

        cart_items.delete()

        FinanceService.add_debt(
            customer,
            total,
            f"Order #{order.id}"
        )

        return order

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
        valid_statuses = ['PENDING', 'CONFIRMED', 'PREPARING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        # منطق تغییر وضعیت (اجازه نده از هر وضعیتی به هر وضعیتی بره)
        status_flow = {
            'PENDING': ['CONFIRMED', 'CANCELLED'],
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