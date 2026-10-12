from django.core.management.base import BaseCommand

from apps.customers.models import Customer
from apps.customers.services import sync_customer_backup


class Command(BaseCommand):
    help = "بکاپ کامل از تمام مشتریان فعال می‌سازد یا آن‌ها را به‌روزرسانی می‌کند."

    def handle(self, *args, **options):
        customers = Customer.objects.select_related('user', 'distributor').all()
        count = 0
        for customer in customers:
            sync_customer_backup(customer)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Backup synced for {count} customers."))