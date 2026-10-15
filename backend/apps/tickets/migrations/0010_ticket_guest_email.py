from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0009_ticket_guest_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="guest_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
    ]
