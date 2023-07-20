# Generated by Django 4.0 on 2023-06-28 18:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("app_invoice", "0001_initial"),
        ("app_order", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="invoices",
                to="app_order.order",
                verbose_name="заказ",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="paid_item",
            field=models.ManyToManyField(
                related_name="invoice_item",
                to="app_order.OrderItem",
                verbose_name="оплаченный товар",
            ),
        ),
    ]
