from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User


class DashboardAccessTests(TestCase):
    def test_dashboard_requires_authentication(self):
        response = APIClient().get('/api/dashboard/')
        self.assertIn(response.status_code, (401, 403))

    def test_admin_can_load_empty_dashboard(self):
        user = User.objects.create_user(
            username='dashboard-admin',
            password='test-password-123',
            role=User.Role.ADMIN,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('today', response.data)
