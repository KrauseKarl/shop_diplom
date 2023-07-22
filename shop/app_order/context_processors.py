"""Модуль содержит контекст-процессоры заказов."""
from app_order.services import order_services


def customer_order_list(request) -> dict:
    """
    Функция возвращает словарь с заказами.

    ['orders'] - список всех заказов покупателя,
    ['new_order'] - список всех заказов со статусом 'НОВЫЙ',
    ['ready_order'] - список всех заказов со статусом 'ГОТОВЫЙ',
    :param request:request
    :return: словарь
    """
    if request.user.is_authenticated and request.user.profile.is_customer:
        orders = order_services.CustomerOrderHandler.get_customer_order_list(
            user=request.user
        )
        new_order = orders.filter(status="created")
        ready_order = orders.filter(status="is_ready")
        return {
            "order": orders,
            "new_order": new_order,
            "ready_order": ready_order,
        }
    else:
        return {"order": None}


def seller_order_list(request) -> dict:
    """
    Функция возвращает словарь заказов продавца.

    ['orders'] - список всех заказов продавца,
    ['all_order_amount'] - кол-во всех заказов
        продавца со статусом 'НОВЫЙ',
    :param request:request
    :return: словарь
    """
    if request.user.is_authenticated and request.user.profile.is_seller:
        all_order_list = (
            order_services.SellerOrderHAndler.get_seller_order_list(
                request.user.id
            )
        )
        order_total_amount = (
            order_services.SellerOrderHAndler.get_order_total_amount(
                request.user.id
            )
        )
        reviews = order_services.SellerOrderHAndler.get_seller_comment_amount(
            request
        )
        return {
            "orders": all_order_list,
            "all_new_order_amount": order_total_amount,
            "reviews": reviews,
        }
    else:
        return {"orders": None, "all_new_order_amount": None, "reviews": None}
