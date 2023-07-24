"""
Модуль содержит сервисы работы с магазинами.

1. StoreHandler - класс для работы с магазином.
2. AdminStoreHandler - класс для работы с магазином
                        со стороны администратора.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, QuerySet
from django.http import Http404

from app_order.models import OrderItem
from app_store.models import Store
from app_item.models import Item

from app_item.services.item_services import ItemHandler


class StoreHandler:
    """Класс для работы с магазином."""

    @staticmethod
    def total_profit_store(store) -> int:
        """
        Функция возвращает общую сумму проданных товаров в магазине.

        :param store - магазин (экземпляр класса Store),
        :return total_profit - сумму всех проданных товаров.
        """
        return OrderItem.objects.filter(
                item__item__store=store
            ).aggregate(
                total_profit=Sum("total")
            ).get(
                "total_profit", 0
            )

    @staticmethod
    def get_store(store_id: int):
        """
        Функция возвращает  магазин (экземпляр класса Store).

        :param store_id - id магазина,
        :return store - экземпляр класса Store.
        """
        try:
            store = Store.active_stores.filter(id=store_id).first()
            return store
        except ObjectDoesNotExist:
            return Http404("Такого магазина не сущесмтвет")

    @staticmethod
    def get_all_story_by_owner(owner: QuerySet[User]) -> QuerySet[Store]:
        """
        Функция возвращает все магазины собственника.

        :param owner - собственник магазина,
        :return my_stores - все магазины собственника.
        """
        my_stores = Store.objects.filter(owner=owner)
        return my_stores

    @staticmethod
    def ordering_store_items(
            queryset: QuerySet[Item], order_by: str
    ) -> QuerySet[Item]:
        """
        Функция возвращает queryset товаров.

        Сортирует queryset товаров по заданому знчению сортировки.
        :param queryset: queryset товаров
        :param order_by: параметр сортировки
        """
        sort_book = {
            "best_seller": ItemHandler.get_bestseller(queryset),
            "best_view": ItemHandler.get_popular_items(queryset),
            "best_comment": ItemHandler.get_comments_items(queryset),
            "stock": queryset.order_by("stock"),
            "-stock": queryset.order_by("-stock"),
            "limited_edition": queryset.filter(
                stock__range=(0, 19)
            ).order_by("-stock"),
            "rest": queryset.filter(stock__lt=5).order_by("-stock"),
        }
        return sort_book[order_by]

    @staticmethod
    def ordering_message(order_by: str) -> str:
        """Функция возвращает название сортировки."""
        message_book = {
            "best_seller": "продажам",
            "best_view": "просмотрам",
            "stock": "количеству на складе  (по возрастанию)",
            "-stock": "количеству на складе (по убыванию)",
            "best_comment": "комментариев",
            "limited_edition": "ограниченному тиражу",
            "rest": "остаткам",
        }
        return message_book[order_by]


class AdminStoreHandler:
    """Класс для работы с магазином со стороны администратора."""

    @staticmethod
    def stores_count() -> int:
        """Функция возвращает общеее кол-во магазинов для админ панели."""
        return (
            Store.objects.values_list("is_active", flat=True)
            .filter(is_active=True)
            .count()
        )
