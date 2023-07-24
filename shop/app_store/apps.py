"""Модуль содержит имя приложения Магазин(app_store)."""
from django.apps import AppConfig


class AppStoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_store"
