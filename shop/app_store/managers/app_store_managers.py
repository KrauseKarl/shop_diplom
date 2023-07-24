"""Модуль содержит менеджеры для работы с набором запросов магазинов."""
from django.db import models


class StoreIsActiveManager(models.Manager):
    """Менеджер для активных магазинов товаров."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class AvailableItemManager(models.Manager):
    """Менеджер для доступных товаров."""

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)
