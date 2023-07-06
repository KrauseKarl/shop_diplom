from django.db import models
from django.db.models import Q


# ITEM MANAGERS #
class AvailableItemManager(models.Manager):
    """Менеджер для доступных товаров."""

    def get_queryset(self):
        return super().get_queryset().filter(
            Q(is_available=True) &
            Q(stock__gt=0)
        )


class UnavailableItemManager(models.Manager):
    """Менеджер для недоступных товаров."""

    def get_queryset(self):
        return super().get_queryset().filter(is_available=False)


class LimitedEditionManager(models.Manager):
    """Менеджер для недоступных товаров."""

    def get_queryset(self):
        return super().get_queryset().filter(limited_edition=True)


# CATEGORY MANAGERS #
class CategoryWithItemsManager(models.Manager):
    """Менеджер для категорий с товарами."""

    def get_queryset(self):
        return super().get_queryset().exclude(
            Q(items=None) &
            Q(sub_categories=None)
        )


class CategoryActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


# COMMENT MANAGERS #
class ModeratedCommentsManager(models.Manager):
    """Менеджер комментариев прошедших модерацию."""

    def get_queryset(self):
        return super().get_query_set().filter(is_published=True)


# TAG MANAGERS #
class AvailableTagManager(models.Manager):
    """Менеджер для доступных тегов."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# FEATURES #
class AvailableFeatureManager(models.Manager):
    """Менеджер для доступных характеристик."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# VALUES #
class AvailableValueManager(models.Manager):
    """Менеджер для доступных знаенчий характеристик."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
