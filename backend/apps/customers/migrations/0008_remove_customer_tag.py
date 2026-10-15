from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0007_customer_shop_name_customerbackup'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='tag',
        ),
        migrations.RemoveField(
            model_name='customerbackup',
            name='tag',
        ),
    ]