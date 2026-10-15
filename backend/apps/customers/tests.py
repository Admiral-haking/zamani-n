from django.test import TestCase
from rest_framework.test import APIClient


class CustomerAccessTests(TestCase):
    def test_customers_require_authentication(self):
        response = APIClient().get('/api/customers/')
        self.assertIn(response.status_code, (401, 403))
