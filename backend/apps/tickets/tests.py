from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.tickets.models import Ticket


class PublicTicketWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username="ticket_staff", password="Secret123!", phone="09120000001",
            national_code="1000000001", role=User.Role.SECRETARY,
        )

    def test_contact_form_is_visible_in_staff_inbox(self):
        response = self.client.post(
            "/api/tickets/contact-messages/submit/",
            {"full_name": "مهمان تست", "email": "guest@example.com", "phone": "09120000002", "subject": "support", "message": "کمک لازم دارم"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.client.force_authenticate(self.staff)
        inbox = self.client.get("/api/tickets/contact-messages/")
        self.assertEqual(inbox.status_code, 200)
        self.assertEqual(inbox.data[0]["email"], "guest@example.com")

    def test_guest_chat_can_be_replied_to_and_closed(self):
        response = self.client.post(
            "/api/tickets/support-chats/send/",
            {"guest_key": "test-chat-key", "guest_name": "مهمان", "text": "سلام"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        ticket_id = response.data["chat_id"]
        self.client.force_authenticate(self.staff)
        response = self.client.post(f"/api/tickets/support-chats/{ticket_id}/reply/", {"text": "پاسخ"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["messages"]), 2)
        response = self.client.post(f"/api/tickets/support-chats/{ticket_id}/close/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Ticket.Status.CLOSED)
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/tickets/support-chats/send/",
            {"guest_key": "test-chat-key", "guest_name": "مهمان جدید", "text": "پیگیری دوباره"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        reopened = Ticket.objects.get(pk=ticket_id)
        self.assertEqual(reopened.status, Ticket.Status.OPEN)
        self.assertEqual(reopened.guest_name, "مهمان جدید")
