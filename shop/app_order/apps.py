"""Модуль содержит имя приложения Заказ(app_order)."""
from django.apps import AppConfig


class AppOrderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_order"