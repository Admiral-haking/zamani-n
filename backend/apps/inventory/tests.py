from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.inventory.models import InventoryLog


class InventoryLogPersistenceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='inventory_staff', password='Secret123!', role=User.Role.SECRETARY,
        )
        self.client.force_authenticate(self.staff)

    def test_log_is_saved_and_can_be_read_after_refresh(self):
        response = self.client.post(
            '/api/inventory/logs/',
            {
                'product': 'همبرگر ۹۰٪ ۱۰۰ گرمی',
                'category': '90',
                'unit': 'package',
                'quantity': 4,
                'direction': '+',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(InventoryLog.objects.count(), 1)

        listed = self.client.get('/api/inventory/logs/?page_size=500')
        self.assertEqual(listed.status_code, 200)
        rows = listed.data['results'] if isinstance(listed.data, dict) else listed.data
        self.assertEqual(rows[0]['product'], 'همبرگر ۹۰٪ ۱۰۰ گرمی')
        self.assertEqual(rows[0]['quantity'], 4)
