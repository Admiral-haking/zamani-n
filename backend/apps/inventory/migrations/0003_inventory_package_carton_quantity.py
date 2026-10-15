from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_inventorylog"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventory",
            name="package_quantity",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="inventory",
            name="carton_quantity",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
