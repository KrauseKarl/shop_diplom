# Generated by Django 4.0 on 2023-03-16 11:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_cart', '0011_alter_cartitem_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='order',
        ),
    ]
