# Generated by Django 4.0 on 2023-01-24 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_item', '0003_feature_alter_item_image_featurevalue_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='featurevalue',
            name='slug',
            field=models.SlugField(default=1, max_length=100, verbose_name='slug'),
            preserve_default=False,
        ),
    ]
