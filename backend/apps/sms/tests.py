from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.sms.models import SmsMessage


class SmsPersistenceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='sms_staff', password='Secret123!', role=User.Role.SECRETARY,
        )
        self.client.force_authenticate(self.staff)

    def test_single_sms_is_persisted(self):
        response = self.client.post(
            '/api/sms/send/',
            {'phone': '۰۹۱۲۳۴۵۶۷۸۹', 'subject': 'تست', 'body': 'پیام آزمایشی'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        message = SmsMessage.objects.get(pk=response.data['data']['id'])
        self.assertEqual(message.phone, '09123456789')
        self.assertEqual(message.body, 'پیام آزمایشی')

    def test_bulk_sms_is_persisted_for_active_customers(self):
        customer_user = User.objects.create_user(
            username='sms_customer', password='Secret123!', role=User.Role.CUSTOMER,
        )
        customer = Customer.objects.get(user=customer_user)
        customer.phone = '09120000001'
        customer.company_name = 'مشتری تست'
        customer.save(update_fields=['phone', 'company_name'])

        response = self.client.post(
            '/api/sms/send_bulk/',
            {'group': 'active', 'subject': 'تست گروهی', 'body': 'پیام گروهی'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(SmsMessage.objects.filter(phone='09120000001', body='پیام گروهی').exists())
