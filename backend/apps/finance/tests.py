from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from .serializers import CheckSerializer


class CheckSerializerTests(TestCase):
    def test_checks_require_authentication(self):
        response = APIClient().get('/api/finance/checks/')
        self.assertIn(response.status_code, (401, 403))

    def test_check_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            CheckSerializer().validate({
                'amount': Decimal('0'),
                'issue_date': date(2026, 1, 2),
                'due_date': date(2026, 1, 3),
            })

    def test_due_date_cannot_precede_issue_date(self):
        with self.assertRaises(ValidationError):
            CheckSerializer().validate({
                'amount': Decimal('1000'),
                'issue_date': date(2026, 1, 3),
                'due_date': date(2026, 1, 2),
            })
