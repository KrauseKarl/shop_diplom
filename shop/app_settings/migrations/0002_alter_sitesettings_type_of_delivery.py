# Generated by Django 4.0 on 2023-06-09 00:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_settings', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='type_of_delivery',
            field=models.CharField(choices=[('обычная доставка', 'Standard'), ('экспресс доставка', 'Express'), ('самовывоз', 'Oneself')], default='standard', max_length=256, verbose_name='тип доставки'),
        ),
    ]
