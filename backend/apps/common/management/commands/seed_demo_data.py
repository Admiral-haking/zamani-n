from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.inventory.models import Inventory
from apps.products.models import Category, Product


class Command(BaseCommand):
    help = "Create idempotent demo users, products, categories, and inventory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            dest="password",
            help="Password for demo users. Required; never uses a hardcoded password.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options.get("password")
        if not password or len(password) < 8:
            raise CommandError("Provide --password with at least 8 characters.")

        users = [
            ("demo_admin", "ADMIN", "09120000001", "demo-admin@example.com", True),
            ("demo_customer", "CUSTOMER", "09120000002", "demo-customer@example.com", False),
        ]
        for username, role, phone, email, is_staff in users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": role,
                    "phone": phone,
                    "email": email,
                    "is_staff": is_staff,
                    "is_superuser": role == "ADMIN",
                    "is_active": True,
                },
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])

        admin = User.objects.get(username="demo_admin")
        categories = {
            "همبرگر": [
                ("DEMO-H90", "همبرگر تستی ۹۰ درصد", 500, 90, 250000, 35, 50),
                ("DEMO-H60", "همبرگر تستی ۶۰ درصد", 500, 60, 220000, 0, 30),
            ],
            "استیک و رست": [
                ("DEMO-STK", "استیک تستی", 400, 100, 380000, 10, 20),
                ("DEMO-RST", "رست بیف تستی", 450, 100, 420000, 5, 15),
            ],
        }
        for category_name, products in categories.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for code, name, weight, meat_percent, price, discount, quantity in products:
                product, _ = Product.objects.update_or_create(
                    code=code,
                    defaults={
                        "category": category,
                        "name": name,
                        "weight": weight,
                        "meat_percent": meat_percent,
                        "base_price": price,
                        "discount_percent": discount,
                        "is_featured": discount > 0,
                        "is_active": True,
                    },
                )
                Inventory.objects.update_or_create(
                    product=product,
                    defaults={"quantity": quantity, "minimum_stock": 10},
                )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Users: demo_admin and demo_customer")
        self.stdout.write("Products: DEMO-H90, DEMO-H60, DEMO-STK, DEMO-RST")
