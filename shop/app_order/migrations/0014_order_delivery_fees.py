# Generated by Django 4.0 on 2023-03-12 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_order', '0013_remove_order_store_order_store'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_fees',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='сумма доставки'),
        ),
    ]
