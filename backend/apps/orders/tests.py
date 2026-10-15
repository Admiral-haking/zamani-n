from django.test import TestCase
from rest_framework.test import APIClient


class OrderAccessTests(TestCase):
    def test_orders_require_authentication(self):
        response = APIClient().get('/api/orders/')
        self.assertIn(response.status_code, (401, 403))
