"""Модуль содержит имя приложения Настроки(app_settings)."""
from django.apps import AppConfig


class AppSettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_settings"
