from django.db import migrations
import re


def backfill_debt_recorded(apps, schema_editor):
    """فاکتورهایی که پیش از افزودن پرچم debt_recorded بدهی‌شان ثبت شده بود.

    با این کار بدهی‌های واقعی و قدیمی در جدول‌های بدهی و کیف پول دوباره دیده
    می‌شوند؛ چون پرچم جدید برای آن‌ها False پیش‌فرض است.
    """
    Order = apps.get_model("orders", "Order")
    Transaction = apps.get_model("finance", "Transaction")

    debt_txs = Transaction.objects.filter(transaction_type="ORDER_DEBT")

    order_ids = set(
        debt_txs.exclude(order__isnull=True).values_list("order_id", flat=True)
    )

    for tx in debt_txs.filter(order__isnull=True):
        match = re.search(r"Order\s*#(\d+)", tx.description or "")
        if not match:
            continue
        order_id = int(match.group(1))
        if Order.objects.filter(id=order_id).exists():
            order_ids.add(order_id)

    if order_ids:
        Order.objects.filter(
            id__in=order_ids,
            debt_recorded=False,
        ).update(debt_recorded=True)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0008_order_debt_recorded_alter_order_status"),
        ("finance", "0006_transaction_order"),
    ]

    operations = [
        migrations.RunPython(backfill_debt_recorded, migrations.RunPython.noop),
    ]