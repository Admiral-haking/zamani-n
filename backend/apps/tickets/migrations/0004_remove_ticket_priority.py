from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_ticket_guest_name_ticket_guest_phone_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='priority',
        ),
    ]