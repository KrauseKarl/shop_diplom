# Generated by Django 4.0 on 2022-11-03 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(choices=[('ADM', 'администратор'), ('SLR', 'продавец'), ('CSR', 'покупатель')], default='CSR', max_length=3, verbose_name='роль'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(default='', upload_to='avatar/', verbose_name='аватар'),
        ),
    ]
