"""Модуль содержит имя приложения Корзина(app_cart)."""
from django.apps import AppConfig


class AppCartConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_cart"
