"""
Run ONCE on the host AFTER: python manage.py migrate
Creates/updates the 4 panel users with their roles and passwords.

Usage (from backend folder):
    python scripts/create_users.py
"""
import os
import sys
import argparse

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.models import User

parser = argparse.ArgumentParser()
for username in ('admin', 'secretary', 'distributor', 'customer'):
    parser.add_argument(f'--{username}-password', required=False)
args = parser.parse_args()
demo_password = os.environ.get("SEED_DEMO_PASSWORD")

CREDS = [
    {"username": "admin", "password": args.admin_password or os.environ.get("SEED_ADMIN_PASSWORD") or demo_password, "role": User.Role.ADMIN, "is_staff": True, "is_superuser": True},
    {"username": "secretary", "password": args.secretary_password or os.environ.get("SEED_SECRETARY_PASSWORD") or demo_password, "role": User.Role.SECRETARY, "is_staff": True, "is_superuser": False},
    {"username": "distributor", "password": args.distributor_password or os.environ.get("SEED_DISTRIBUTOR_PASSWORD") or demo_password, "role": User.Role.DISTRIBUTOR, "is_staff": False, "is_superuser": False},
    {"username": "customer", "password": args.customer_password or os.environ.get("SEED_CUSTOMER_PASSWORD") or demo_password, "role": User.Role.CUSTOMER, "is_staff": False, "is_superuser": False},
]

missing = [item['username'] for item in CREDS if not item['password'] or len(item['password']) < 8]
if missing:
    raise SystemExit('Set a password of at least 8 characters for: ' + ', '.join(missing))

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
