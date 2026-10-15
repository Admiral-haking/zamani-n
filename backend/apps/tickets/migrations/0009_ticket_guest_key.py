from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('tickets', '0008_backfill_initial_messages')]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='guest_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=120),
        ),
    ]
