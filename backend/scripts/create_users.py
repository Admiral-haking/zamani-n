"""
Run ONCE on the host AFTER: python manage.py migrate
Creates/updates the 4 panel users with their roles and passwords.

Usage (from backend folder):
    python scripts/create_users.py
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.models import User

CREDS = [
    {"username": "admin",       "password": "Admin@1404", "role": User.Role.ADMIN,       "is_staff": True,  "is_superuser": True},
    {"username": "secretary",   "password": "Sec@1404",   "role": User.Role.SECRETARY,   "is_staff": True,  "is_superuser": False},
    {"username": "distributor", "password": "Dist@1404",  "role": User.Role.DISTRIBUTOR, "is_staff": False, "is_superuser": False},
    {"username": "customer",    "password": "Cust@1404",  "role": User.Role.CUSTOMER,    "is_staff": False, "is_superuser": False},
]

for item in CREDS:
    user, created = User.objects.update_or_create(
        username=item["username"],
        defaults={
            "role": item["role"],
            "is_active": True,
            "is_staff": item["is_staff"],
            "is_superuser": item["is_superuser"],
        },
    )
    user.set_password(item["password"])
    user.save(update_fields=["password", "role", "is_active", "is_staff", "is_superuser"])
    print(("CREATED " if created else "UPDATED ") + item["username"] + " -> role=" + item["role"])

print("Done. 4 users are ready.")