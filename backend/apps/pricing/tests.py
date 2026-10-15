from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.products.models import Product


class CustomerPricingWorkflowTests(TestCase):
    def setUp(self):
        self.distributor = User.objects.create_user(
            username="pricing_dist", password="Secret123!", phone="09120000005",
            national_code="1000000005", role=User.Role.DISTRIBUTOR,
        )
        self.customer = User.objects.create_user(
            username="pricing_customer", password="Secret123!", phone="09120000006",
            national_code="1000000006", role=User.Role.CUSTOMER,
        )
        profile = self.customer.customer_profile
        profile.distributor = self.distributor.distributor_profile
        profile.save()
        self.product = Product.objects.create(
            code="TEST-PRICE", name="محصول قیمت تست", weight=100,
            meat_percent=90, base_price=1000,
        )
        self.client = APIClient()

    def test_distributor_can_bulk_save_read_and_delete_customer_price(self):
        self.client.force_authenticate(self.distributor)
        payload = {"customer": self.customer.customer_profile.id, "prices": [{"product": self.product.id, "price": 800}]}
        response = self.client.post("/api/pricing/customer-prices/bulk/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created"], 1)

        response = self.client.get(f"/api/pricing/customer-prices/?customer={payload['customer']}")
        self.assertEqual(response.status_code, 200)
        rows = response.data.get("results", response.data)
        self.assertEqual(len(rows), 1)

        response = self.client.delete(f"/api/pricing/customer-prices/{rows[0]['id']}/")
        self.assertEqual(response.status_code, 204)
