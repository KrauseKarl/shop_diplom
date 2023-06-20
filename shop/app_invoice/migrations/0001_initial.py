# Generated by Django 4.0 on 2023-06-20 20:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_order', '0003_order_archived'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_purchase_sum', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='сумма товаров')),
                ('delivery_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='стоимость доставки')),
                ('total_sum', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='итоговая сумма')),
                ('number', models.CharField(max_length=20, verbose_name='номер платежного документа')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='дата создания')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='app_order.order', verbose_name='чек')),
                ('paid_item', models.ManyToManyField(related_name='invoices', to='app_order.OrderItem', verbose_name='плаченный товар')),
            ],
            options={
                'verbose_name': 'квитанция',
                'verbose_name_plural': 'квитанции',
                'db_table': 'app_invoices',
                'ordering': ['-created'],
            },
        ),
    ]
