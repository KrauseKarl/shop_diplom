"""Модуль содержит контекст-процессоры корзины и товаров в корзине."""
from app_cart.services import cart_services as service


def get_cart(request) -> dict:
    """
    Функция возвращает словарь с данными корзины.

    Словарь  состоит:
        - из корзины,
        - словаря (товары отсортированные по магазинам,
            общая стоимость и стоимость доставки)
        - общей стоимости доставки
    """
    cart_dict = service.get_current_cart(request)
    return {"cart_dict": cart_dict}


def in_cart(request) -> dict:
    """
    Функция определяем какие товары в корзине.

    Все товары каталога,которые находятся уже
    в корзине будут иметь надпись "В КОРЗИНЕ".
    """
    return {"in_cart": service.get_items_in_cart(request)}
