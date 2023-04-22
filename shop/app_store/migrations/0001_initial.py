# Generated by Django 4.0 on 2023-04-09 11:22

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=200, verbose_name='название магазина')),
                ('slug', models.SlugField(max_length=100, verbose_name='slug')),
                ('discount', models.SmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99), django.core.validators.MinValueValidator(0)], verbose_name='скидка')),
                ('min_for_discount', models.DecimalField(decimal_places=2, default=0, max_digits=9, verbose_name='минимальная сумма бесплатной доставки')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='дата создания')),
                ('updated', models.DateTimeField(auto_now_add=True, verbose_name='дата обновления')),
                ('description', models.TextField(blank=True, default='', verbose_name='Описание магазина')),
                ('logo', models.ImageField(blank=True, default='default_images/default_store.jpg', upload_to='store/logo/')),
                ('is_active', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='store', to='auth.user', verbose_name='собственник')),
            ],
            options={
                'verbose_name': 'магазин',
                'verbose_name_plural': 'магазины',
                'db_table': 'app_store',
                'ordering': ['created'],
            },
        ),
    ]
