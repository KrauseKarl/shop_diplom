# Generated by Django 4.0 on 2023-06-28 18:14

import app_user.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("app_item", "0002_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=False, verbose_name="активный профиль"),
                ),
                (
                    "avatar",
                    models.ImageField(
                        default="",
                        upload_to=app_user.models.user_dir_path,
                        verbose_name="аватар",
                    ),
                ),
                (
                    "telephone",
                    models.CharField(
                        max_length=18, unique=True, verbose_name="телефон"
                    ),
                ),
                ("date_joined", models.DateTimeField(auto_now_add=True, null=True)),
                (
                    "review_items",
                    models.ManyToManyField(
                        related_name="item_views", to="app_item.Item"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to="auth.user",
                        verbose_name="пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "профиль",
                "verbose_name_plural": "профили",
                "ordering": ["user"],
            },
        ),
    ]
