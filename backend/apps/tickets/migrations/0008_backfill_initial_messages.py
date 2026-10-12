from django.db import migrations


def backfill_initial_messages(apps, schema_editor):
    Ticket = apps.get_model("tickets", "Ticket")
    TicketMessage = apps.get_model("tickets", "TicketMessage")

    for ticket in Ticket.objects.filter(
        message__isnull=False
    ).exclude(message=""):
        if ticket.messages.exists():
            continue
        TicketMessage.objects.create(
            ticket=ticket,
            sender="GUEST" if ticket.user_id is None else "CUSTOMER",
            sender_name=ticket.guest_name or "",
            text=ticket.message,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0007_ticketattachment"),
    ]

    operations = [
        migrations.RunPython(backfill_initial_messages, migrations.RunPython.noop),
    ]