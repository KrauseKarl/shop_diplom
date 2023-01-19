from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum

from app_item.services.item_services import ItemHandler
from app_order.models import Invoice, Store


class StoreHandler:
    @classmethod
    def total_profit_store(cls, store) -> int:
        """
        Функция возвращает общую сумму проданных товаров в магазине.
        :param store - магазин (экземпляр класса Store),
        :return total_profit - сумму всех проданных товаров.
        """
        return Invoice.objects.filter(recipient=store).select_related('order').aggregate(
            total_profit=Sum('order__total_sum')).get('total_profit', 0)

    @classmethod
    def get_store(cls, store_id):
        """
        Функция возвращает  магазин (экземпляр класса Store).
        :param store_id - id магазина,
        :return store - экземпляр класса Store.
        """
        try:
            store = Store.active_stores.filter(id=store_id).first()
            return store
        except ObjectDoesNotExist:
            return None

    @classmethod
    def get_all_story_by_owner(cls, owner):
        """
        Функция возвращает  магазины (экземпляр класса Store).
        :param owner - собственник магазина,
        :return my_stores - все магазины собственника.
        """
        my_stores = Store.objects.filter(owner=owner)
        return my_stores

    @staticmethod
    def ordering_store_items(queryset, order_by):
        sort_book = {
            'best_seller': ItemHandler.get_bestseller(queryset),
            'best_view': ItemHandler.get_popular_items(queryset),
            'best_comment': ItemHandler.get_comments_items(queryset),
            'stock': queryset.order_by('stock'),
            'limited_edition': queryset.filter(stock__range=(6, 16)).order_by('-stock'),
            'rest': queryset.filter(stock__lt=5).order_by('-stock'),
        }
        return sort_book[order_by]

    @staticmethod
    def ordering_message(order_by):
        message_book = {
            'best_seller': 'продажам',
            'best_view': 'просмотрам',
            'stock': 'количеству на складе',
            'best_comment': 'комментариев',
            'limited_edition': 'ограниченному тиражу',
            'rest': 'остаткам'
        }
        return message_book[order_by]
