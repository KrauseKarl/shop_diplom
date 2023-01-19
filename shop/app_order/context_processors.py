from app_cart.models import CartItem
from app_item.models import Item
from app_order.models import Order
from django.core.exceptions import ObjectDoesNotExist

from app_store.models import Store


def order_list(request):
    # TODO order_list description
    try:
        order = Order.objects.filter(user=request.user, status='new').order_by('-created').first()
        return {'order': order}
    except ObjectDoesNotExist:
        return {'order': None}


def all_store_order(request):
    # TODO all_store_order description
    try:
        # собственник
        owner = request.user

        # все магазины собственника
        stores = Store.objects.select_related('owner').filter(owner=owner)

        # все товары в магазинах собственника
        items = Item.objects.select_related('store').filter(store__in=stores)

        # все заказанные товары из магазинов
        items_in_cart = CartItem.objects.select_related('item').filter(item_id__in=items)

        # all sold product
        items_my_store = items.filter(cart_item__in=items_in_cart)

        # все заказы в магазинах собственника
        all_orders = Order.objects.select_related('user', 'store').filter(items_is_paid__in=items_in_cart)

        # кол-во всех заказов со статусами ('new', 'in_progress')
        all_order_amount = all_orders.values_list('status').filter(status__in=('new', 'in_progress')).count()

        return {'all_order': all_orders, 'all_order_amount': all_order_amount, 'orders': all_orders}
    except (ObjectDoesNotExist, TypeError):
        return {'all_order': None, 'all_order_amount': 0, 'orders': None}
