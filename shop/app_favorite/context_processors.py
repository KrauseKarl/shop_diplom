"""Модуль содержит контекст-процессоры списка избранных товаров."""
from app_favorite.favorites import Favorite


def favorites(request) -> dict:
    """
    Функция возвращает словарь с избранными товарами.

    Список избранных товаров и их количество.
    """
    favorites_item = Favorite(request)
    return {
        "favorites_count": favorites_item.__len__(),
        "favorites": favorites_item,
    }
