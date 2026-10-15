from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.finance.models import Check
from apps.tickets.models import Ticket


class PanelPersistenceTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="test-admin",
            password="password123",
            role=User.Role.ADMIN,
            phone="09121111111",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_owner_customer_form_persists_profile_fields(self):
        response = self.client.post(
            "/api/accounts/users/create-customer/",
            {
                "username": "test-customer",
                "password": "password123",
                "first_name": "علی",
                "last_name": "تست",
                "phone": "09122222222",
                "national_code": "0012345678",
                "company_name": "فروشگاه تست",
                "address": "آدرس تست",
                "postal_code": "1234567890",
                "tag": "vip",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        customer = Customer.objects.get(user__username="test-customer")
        self.assertEqual(customer.national_id, "0012345678")
        self.assertEqual(customer.address, "آدرس تست")
        self.assertEqual(customer.postal_code, "1234567890")
        self.assertEqual(customer.tag, "vip")

    def test_ticket_and_check_are_persisted(self):
        customer_user = User.objects.create_user(
            username="check-customer",
            password="password123",
            role=User.Role.CUSTOMER,
            phone="09123333333",
        )
        customer = Customer.objects.get(user=customer_user)
        customer.phone = "09123333333"
        customer.save(update_fields=["phone"])
        ticket_response = self.client.post(
            "/api/tickets/",
            {"title": "تیکت تست", "message": "متن تست", "category": "GENERAL"},
            format="json",
        )
        check_response = self.client.post(
            "/api/finance/checks/",
            {
                "customer": customer.id,
                "check_number": "TEST-CHECK-1",
                "bank_name": "بانک تست",
                "amount": 1000,
                "issue_date": "2026-10-15",
                "due_date": "2026-11-15",
            },
            format="json",
        )
        self.assertEqual(ticket_response.status_code, 201)
        self.assertTrue(Ticket.objects.filter(title="تیکت تست").exists())
        self.assertEqual(check_response.status_code, 201)
        self.assertTrue(Check.objects.filter(check_number="TEST-CHECK-1").exists())

    def test_non_customer_cannot_access_cart(self):
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, 403)
