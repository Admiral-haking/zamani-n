from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('distributors', '0002_distributor_city')]

    operations = [
        migrations.CreateModel(
            name='DistributorPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', models.JSONField(default=list, help_text='لیست اقلام: [{product_id, product_name, unit, quantity, price, total}]')),
                ('total_amount', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('status', models.CharField(choices=[('PENDING', 'در انتظار تایید'), ('CONFIRMED', 'تایید شده'), ('REJECTED', 'رد شده'), ('CANCELLED', 'لغو شده')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('distributor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='distributors.distributor')),
            ],
            options={'db_table': 'distributor_purchases', 'ordering': ['-created_at']},
        ),
    ]
