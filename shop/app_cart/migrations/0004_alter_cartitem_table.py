# Generated by Django 4.0 on 2022-11-13 20:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_cart', '0003_cartitem_cart_items'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='cartitem',
            table='app_items_in_cart',
        ),
    ]
