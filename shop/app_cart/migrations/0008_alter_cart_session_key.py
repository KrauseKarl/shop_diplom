# Generated by Django 4.0 on 2023-01-15 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cart', '0007_alter_cart_is_archived'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='session_key',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='ключ сессии'),
        ),
    ]
