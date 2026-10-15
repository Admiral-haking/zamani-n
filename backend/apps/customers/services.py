# backend/apps/customers/services.py
"""
سرویس بک‌آپ مشتریان:
- sync_customer_backup: هر بار که مشتری ساخته یا ویرایش شود، بک‌آپ به‌روز می‌شود.
- archive_customer_backup: هنگام حذف کامل، قبل از حذف داده، تاریخچه کامل ذخیره می‌شود.
"""
from django.utils import timezone

from .models import CustomerBackup

PAYMENT_METHOD_LABELS = {
    'CASH': 'نقدی',
    'CARD': 'کارت به کارت',
    'ONLINE': 'آنلاین',
    'BALANCE': 'حساب اعتباری',
    'CHECK': 'چک',
}
PAYMENT_STATUS_LABELS = {
    'PENDING': 'در انتظار',
    'SUCCESS': 'موفق',
    'FAILED': 'ناموفق',
}
CHECK_STATUS_LABELS = {
    'PENDING': 'در انتظار',
    'APPROVED': 'تایید شده',
    'REJECTED': 'رد شده',
    'PAID': 'پاس شده',
}


def _customer_display_name(customer):
    if customer.company_name:
        return customer.company_name
    if customer.user_id:
        return customer.user.get_full_name() or customer.user.username
    return f'مشتری #{customer.id}'


def _build_snapshot(customer):
    """عکس کامل از مشتری + تمام سوابق مرتبط."""
    from apps.orders.models import Order
    from apps.finance.models import Check, Transaction
    from apps.tickets.models import Ticket

    snapshot = {
        'customer': {
            'id': customer.id,
            'customer_code': customer.customer_code or '',
            'username': customer.user.username if customer.user_id else '',
            'full_name': _customer_display_name(customer),
            'company_name': customer.company_name or '',
            'shop_name': customer.shop_name or '',
            'phone': customer.phone or '',
            'national_id': customer.national_id or '',
            'address': customer.address or '',
            'city': customer.city or '',
            'state': customer.state or '',
            'postal_code': customer.postal_code or '',
            'distributor_name': customer.distributor.full_name if customer.distributor_id else '',
            'account_balance': str(customer.account_balance),
            'price_list': customer.price_list or {},
            'is_active': customer.is_active,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
        },
        'orders': [],
        'transactions': [],
        'checks': [],
        'return_requests': [],
        'notes': [],
        'tickets': [],
    }

    orders_qs = customer.orders.prefetch_related('items__product', 'payments')
    for order in orders_qs:
        order_data = {
            'id': order.id,
            'invoice_number': order.tracking_code or f'#{order.id}',
            'status': order.status,
            'total_price': str(order.total_price),
            'is_printed': bool(order.is_printed),
            'created_at': order.created_at.isoformat(),
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': str(item.price),
                    'total': str(item.quantity * item.price),
                }
                for item in order.items.all()
            ],
            'payments': [
                {
                    'amount': str(p.amount),
                    'method': PAYMENT_METHOD_LABELS.get(p.method, p.method),
                    'status': PAYMENT_STATUS_LABELS.get(p.status, p.status),
                    'created_at': p.created_at.isoformat(),
                }
                for p in order.payments.all()
            ],
        }
        snapshot['orders'].append(order_data)

    for txn in customer.transactions.all():
        snapshot['transactions'].append({
            'type': txn.transaction_type,
            'amount': str(txn.amount),
            'description': txn.description or '',
            'created_at': txn.created_at.isoformat(),
        })

    checks_qs = Check.objects.filter(customer=customer)
    for ch in checks_qs:
        snapshot['checks'].append({
            'check_number': ch.check_number,
            'bank_name': ch.bank_name,
            'amount': str(ch.amount),
            'issue_date': ch.issue_date.isoformat() if ch.issue_date else None,
            'due_date': ch.due_date.isoformat() if ch.due_date else None,
            'status': CHECK_STATUS_LABELS.get(ch.status, ch.status),
        })

    return_requests = customer.return_requests.all()
    for rr in return_requests:
        snapshot['return_requests'].append({
            'product_name': rr.product_name,
            'quantity': rr.quantity,
            'reason': rr.reason,
            'description': rr.description or '',
            'status': rr.status,
            'created_at': rr.created_at.isoformat(),
        })

    for note in customer.notes.all():
        snapshot['notes'].append({
            'content': note.content,
            'is_important': note.is_important,
            'created_at': note.created_at.isoformat(),
        })

    if customer.user_id:
        for ticket in Ticket.objects.filter(user_id=customer.user_id):
            snapshot['tickets'].append({
                'title': ticket.title,
                'message': ticket.message,
                'category': ticket.category,
                'status': ticket.status,
                'admin_reply': ticket.admin_reply or '',
                'created_at': ticket.created_at.isoformat(),
            })

    return snapshot


def _fill_backup(backup, customer, actor=None, deleted=False):
    snapshot = _build_snapshot(customer)
    backup.original_customer_id = customer.id
    backup.customer_code = customer.customer_code or ''
    backup.username = customer.user.username if customer.user_id else ''
    backup.full_name = _customer_display_name(customer)
    backup.company_name = customer.company_name or ''
    backup.shop_name = customer.shop_name or ''
    backup.phone = customer.phone or ''
    backup.national_id = customer.national_id or ''
    backup.address = customer.address or ''
    backup.city = customer.city or ''
    backup.state = customer.state or ''
    backup.postal_code = customer.postal_code or ''
    backup.distributor_name = customer.distributor.full_name if customer.distributor_id else ''
    backup.account_balance = customer.account_balance
    backup.snapshot = snapshot
    if deleted:
        backup.is_deleted = True
        backup.deleted_at = timezone.now()
        backup.deleted_by = actor
    else:
        backup.is_deleted = False
        backup.deleted_at = None
        backup.deleted_by = None
    if actor and not backup.created_by_id:
        backup.created_by = actor
    backup.save()
    return backup


def sync_customer_backup(customer, actor=None):
    """به‌روزرسانی بک‌آپ یک مشتری فعال (پس از ساخت یا ویرایش)."""
    backup = CustomerBackup.objects.filter(
        original_customer_id=customer.id
    ).first()
    if backup is None:
        backup = CustomerBackup(original_customer_id=customer.id, created_by=actor)
    return _fill_backup(backup, customer, actor=actor)


def archive_customer_backup(customer, actor=None):
    """درج/به‌روزرسانی بک‌آپ با علامت حذف‌شده، قبل از حذف کامل داده‌ها."""
    backup = CustomerBackup.objects.filter(
        original_customer_id=customer.id
    ).first()
    if backup is None:
        backup = CustomerBackup(original_customer_id=customer.id, created_by=actor)
    return _fill_backup(backup, customer, actor=actor, deleted=True)