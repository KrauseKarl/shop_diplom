# Generated by Django 4.0 on 2023-06-21 02:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_order', '0003_order_archived'),
        ('app_invoice', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='app_order.order', verbose_name='заказ'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='paid_item',
            field=models.ManyToManyField(related_name='invoice_item', to='app_order.OrderItem', verbose_name='оплаченный товар'),
        ),
    ]
