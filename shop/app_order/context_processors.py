from app_cart.models import CartItem
from app_item.models import Item, Comment
from app_order.models import Order
from django.core.exceptions import ObjectDoesNotExist

from app_order.services.order_services import CustomerOrderHandler, SellerOrderHAndler
from app_store.models import Store


def customer_order_list(request) -> dict:
    """
    Функция возвращает словарь где значение
    это список всех заказов пользователя
    :param request:request
    :return: словарь
    """
    if request.user.is_authenticated and request.user.profile.is_customer:
        orders = CustomerOrderHandler.get_customer_order_list(request)
        new_order = orders.filter(status='created')
        ready_order = orders.filter(status='is_ready')
        return {'order': orders, 'new_order': new_order, 'ready_order':ready_order}
    else:
        return {'order': None}


def seller_order_list(request) -> dict:
    """
       Функция возвращает словарь где ['orders']
       это список всех заказов продавца,
       ['all_order_amount']
       это кол-во  всех заказов продавца со статусом 'НОВЫЙ',
       :param request:request
       :return: словарь
       """
    if request.user.is_authenticated and request.user.profile.is_seller:
        all_order_list = SellerOrderHAndler.get_seller_order_list(request)
        order_total_amount = SellerOrderHAndler.get_order_total_amount(request)
        reviews = SellerOrderHAndler.get_seller_comment_amount(request)
        return {'orders': all_order_list, 'all_new_order_amount': order_total_amount, 'reviews': reviews}
    else:
        return {'orders': None, 'all_new_order_amount': None, 'reviews': None}

