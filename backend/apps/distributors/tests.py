from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.products.models import Product


class DistributorPurchaseWorkflowTests(TestCase):
    def setUp(self):
        self.distributor_user = User.objects.create_user(
            username="purchase_dist", password="Secret123!", phone="09120000003",
            national_code="1000000003", role=User.Role.DISTRIBUTOR,
        )
        self.product = Product.objects.create(
            code="TEST-PURCHASE", name="محصول تست", weight=100,
            meat_percent=90, base_price=1000,
        )
        self.client = APIClient()

    def test_distributor_purchase_is_created_and_staff_can_confirm(self):
        self.client.force_authenticate(self.distributor_user)
        response = self.client.post(
            "/api/distributors/purchases/",
            {"items": [{"product_id": self.product.id, "product_name": self.product.name, "unit": "package", "quantity": 2, "price": 1000}]},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total_amount"], "2000")
        purchase_id = response.data["id"]

        staff = User.objects.create_user(
            username="purchase_staff", password="Secret123!", phone="09120000004",
            national_code="1000000004", role=User.Role.SECRETARY,
        )
        self.client.force_authenticate(staff)
        response = self.client.post(f"/api/distributors/purchases/{purchase_id}/confirm/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "CONFIRMED")
