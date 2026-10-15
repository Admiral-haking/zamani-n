from django.test import TestCase
from rest_framework.test import APIClient


class DashboardAccessTests(TestCase):
    def test_dashboard_requires_authentication(self):
        response = APIClient().get('/api/dashboard/')
        self.assertIn(response.status_code, (401, 403))
