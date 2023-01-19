from django.core.cache import cache
from django.http.response import HttpResponseBase, HttpResponseRedirect
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum, Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from app_cart.models import *
from app_item.models import Item
from app_item.services.item_services import ItemHandler
from app_store.models import Store
from app_user.services.user_services import is_customer


def cart_(request):
    """Функция возвращает текущую корзину. """

    if request.user.is_authenticated and request.user.profile.is_customer:
        cart = get_auth_user_cart(request)
        if not cart:
            cart = Cart.objects.create(user=request.user)
    else:
        session_key = request.COOKIES.get('cart')
        if session_key:
            cart = get_anon_user_cart(session_key)
        else:
            cart = None
    return cart


def get_current_cart(request) -> dict:
    """
    Функция возвращает словарь из трех ключей(
        - корзина с товарами ('cart'),
        - отсортированные товары по магазинам('book'),
        - стоимость доставки товаров по магазинам('fees')
        )
    :param request:
    :return: словарь
    """
    cart = cart_(request)

    try:
        ordered_cart_by_store = order_items_in_cart(cart)
        items_and_fees = calculate_delivery_fees(ordered_cart_by_store)
        total_delivery_fees = fees_total_amount(items_and_fees)
        return {'cart': cart, 'book': ordered_cart_by_store, 'fees': total_delivery_fees}
    except (KeyError, AttributeError):
        return {'cart': cart}


def add_item_in_cart(request, item_id):
    """
     Функция для добавления товара из корзины.
    :param request: request
    :param item_id: id товара
    :return: response редирект URL источника запроса
    """
    response = redirect(request.META.get('HTTP_REFERER'))
    if request.user.profile.is_customer:
        cart = get_current_cart(request).get('cart')
        item = ItemHandler.get_item(item_id)
        if request.user.is_authenticated:
            # all_cart_item = CartItem.objects.filter(Q(item=item) & Q(is_paid=False))
            # # находим общее кол-во этих товаров для корзины
            # all_cart_item = all_cart_item.aggregate(total_sum=Sum('quantity')).get('total_sum')
            # # сравниваем кол-во в корзине с кол-вом на складе
            # if item.stock == all_cart_item:
            #     item.is_available = False
            #     item.save()
            # # сравниваем кол-во в корзине с кол-вом на складе
            # if item.stock + 1 > all_cart_item + 1:
            # cart_items = get_items_in_cart(request)
            is_already_added = cart.items.filter(item_id=item.id).first()
            if is_already_added:
                cart_item = cart.items.get(item=item)
                cart_item.quantity += 1
                cart_item.save(update_fields=['quantity', 'updated'])
            else:
                cart_item = create_cart_item(item, user=request.user)
                cart.items.add(cart_item)
        else:
            if not cart:
                session_key = create_session_key(request)
                cart, created = Cart.objects.get_or_create(session_key=session_key, is_anonymous=True)
                if created:
                    cart_item = create_cart_item(item)
                    cart.items.add(cart_item)
            else:
                cart_item = cart.items.filter(item=item).first()
                if cart_item:
                    cart_item.quantity += 1
                    cart_item.save(update_fields=['quantity', 'updated'])
                else:
                    cart_item = create_cart_item(item)
                    cart.items.add(cart_item)
            response = set_cart_cookies(request)
        messages.add_message(request, messages.SUCCESS, f'{item} \nдобавлен в вашу корзину')
    return response


def remove_from_cart(request, item_id):
    """
    Функция для удаления товара из корзины.
    :param request: request
    :param item_id: id товара
    :return:
    """
    cart = get_current_cart(request).get('cart')
    cart_item = get_object_or_404(CartItem, id=item_id, is_paid=False)
    messages.add_message(request, messages.SUCCESS, f"{cart_item.item.title} удален из корзины")
    try:
        cart.items.get(id=item_id).delete()
    except ObjectDoesNotExist:
        pass


def update_quantity_item_in_cart(request, quantity, update, **kwargs):
    """
    Функция обновляет кол-во товара в корзине.
    :param request: request
    :param quantity: кол-во товара
    :param update: булевой значение статуса обновления товара
    :param kwargs: item_id id товара
    """
    item_id = kwargs['item_id']
    cart = get_current_cart(request).get('cart')
    if update:
        cart_item = cart.items.get(id=item_id)
        if quantity == 0:
            cart_item.delete()
            messages.add_message(request, messages.SUCCESS, f"Товар удален из корзины")
        else:
            cart_item.quantity = int(quantity)
            cart_item.save()
            messages.add_message(request, messages.SUCCESS, f"Количество товара обновлено до {cart_item.quantity} шт.")


def order_items_in_cart(cart) -> dict:
    """
    Возвращает словарь  товаров в корзине
    отсортированных по магазинам,
    их общую стоимость (total),
    сам товар (product),
    и проверяет соотношение кол-ва каждого товара в корзине
    с кол-вом  товара на складе продавца.
    Если кол-во на складе достаточно, то возвращает ключ('is_not_enough') - False,
    в противном случае - возвращает ключ('is_not_enough') со значением  кол-во товара на складе.
    {'shop_title':
        'items: {
            'total': int(),
            'item_id': {
                'product': QuerySet[Item],
                'is_not_enough': False/item.stock
                }
            },
    }
    """
    # все товары в корзине

    items = cart.items.select_related('item__store').filter(
        Q(item__is_available=True) &
        Q(item__stock__gt=0) &
        Q(is_paid=False)
    ).order_by('-updated')

    sort_by_store = {}
    for cart_item in items:
        # название магазина
        shop = cart_item.item.store
        # кол-во товара на складе для сравнения с кол-вом в корзине
        item_stock = Item.objects.select_related('cart_item') \
            .values_list('stock') \
            .filter(cart_item=cart_item).first()[0]
        # заполняем словарь
        if shop not in sort_by_store:
            # если магазина нет словаре,
            # добавляем вложенный словарь с суммой, товаром и булевым значением
            sort_by_store[shop] = {'total': cart_item.total,
                                   'items': {
                                       f'{cart_item.id}': {
                                           'product': cart_item,
                                           'is_not_enough': False
                                       }
                                   }
                                   }
        else:
            # добавляем сумму к имеющейся сумме всех товаров этого магазина
            sort_by_store[shop]['total'] += cart_item.total
            # если в словаре нет товара - добавляем его
            if not sort_by_store[shop]['items'].get(f'{cart_item.id}'):
                sort_by_store[shop]['items'][f'{cart_item.id}'] = {
                    'product': cart_item,
                    'is_not_enough': False
                }
        # проверяем достаточно ли товара на складе
        # если товара на складе меньше, то меняем булевое-False значение на  кол-во товара
        if cart_item.quantity > item_stock:
            sort_by_store[shop]['items'][f'{cart_item.id}']['is_not_enough'] = item_stock
    return sort_by_store


def calculate_delivery_fees(ordered_cart_by_store):
    """
    Функция определяет если сумма заказа меньше установленного,
    то возвращает стоимость доставки, если же наоборот, то возвращает 0.
    """
    for store, value in ordered_cart_by_store.items():
        total = value['total']
        min_free_delivery = store.min_free_delivery
        if total > min_free_delivery:
            value['fees'] = 0
        else:
            fees = store.delivery_fees
            value['fees'] = fees
    return ordered_cart_by_store


def fees_total_amount(book):
    """Функция определяет общую стоимость доставки для всех товаров в корзине."""
    return sum(value['fees'] for key, value in book.items())


def get_auth_user_cart(request):
    """Функция возвращает корзину пользователя."""
    cart = Cart.objects.filter(Q(user=request.user) & Q(is_archived=False)).first()
    return cart


def get_anon_user_cart(session_key):
    """Функция возвращает корзину анонимного пользователя."""
    cart = Cart.objects.filter(
        Q(is_anonymous=True) & Q(is_archived=False) & Q(session_key=session_key)).first()
    return cart


def create_cart_item(item, user=None):
    """Функция создает экземпляр 'CartItem'."""
    cart_item = CartItem.objects.create(item=item, price=item.price, is_paid=False, user=user)
    return cart_item


def merge_anon_cart_with_user_cart(request, cart):
    """
    Функция для слияния корзины анонимного пользователя
    с корзиной зарегистрированного пользователя.
        :param request: request
        :param cart: текущая корзина зарегистрированного пользователя
        :return: корзина зарегистрированного пользователя
        объединенная с товарами из анонимной корзины.
    """
    try:
        session_key = request.COOKIES.get('cart')
        # получаем из сессий корзину анонимного пользователя
        anonymous_cart = get_anon_user_cart(session_key)
        # 'перекладываем' все товары из анонимной корзины в новую корзину
        if anonymous_cart:
            items_from_anon_cart = anonymous_cart.items.prefetch_related('item').all()
            for cart_item in items_from_anon_cart:
                cart_item.user = request.user
                cart_item.save()
                already_in_cart_item = cart.items.filter(item__id=cart_item.item.id).first()
                if already_in_cart_item:
                    already_in_cart_item.quantity += cart_item.quantity
                    already_in_cart_item.save()
                else:
                    cart.items.add(cart_item)
            # удаляем анонимную корзину
            anonymous_cart.delete()
    except KeyError:
        pass


def get_items_in_cart(request):
    """
    Функция возвращает все товары, которые выбрал пользователь.
    Информация о товарах используется, для корректного отображения
    значка "В КОРЗИНЕ" в каталоге товаров.
    """
    try:
        items_in_cart = get_current_cart(request).get('cart').items.all()
        in_cart = Item.objects.filter(cart_item__in=items_in_cart)
    except AttributeError:
        in_cart = None
    return in_cart


def create_session_key(request):
    """Функция создает ключ и сохраняет его в сессии."""
    if not request.session.session_key:
        session_key = request.session.save()

    return request.session.session_key


def create_cart(request, path=None):
    """
    Функция создает корзину для анонимного пользователя.

    :param request: request
    :param path: редирект URL источника запроса
    :return: response.
    """
    session_key = request.COOKIES.get('cart')
    cart_id = None
    if not request.user.is_authenticated:
        if not session_key:
            session_key = create_session_key(request)
            cart, created = Cart.objects.get_or_create(session_key=session_key, is_anonymous=True)
            if created:
                path = 'app_cart:cart'
                cart_id = cart.pk
            else:
                path = request.META.get('HTTP_REFERER')
    response = set_cart_cookies(request, session_key, path, cart_id)
    return response


def set_cart_cookies(request, session_key=None, path=None, cart_id=None):
    """
    Функция устанавливает cookies['cart'] с session_key анонимной корзины и
        cookies['has_cart']=True на 1 год(max_age=31536000).

        :param request: request
        :param session_key: ключ-сессии анонимной корзины
        :param path: путь для response
        :param cart_id: id корзины анонимной корзины
        :return: response.
    """
    if not path:
        path = request.META.get('HTTP_REFERER')
    if cart_id:
        response = redirect('app_cart:cart', cart_id)
    else:
        response = redirect(path)

    session_cart = request.COOKIES.get('cart')
    if not session_cart:
        response.set_cookie("has_cart", True)
        if not session_key:
            session_key = create_session_key(request)
        response.set_cookie("cart", session_key, max_age=31536000)
    return response


def delete_cart_cookies(request, path):
    """
    Функция удаляет cookies['cart'].

    вызывает функцию для слияния анонимной корзины и корзины пользователя.
    удаляет cookies['cart'] и cookies['has_cart'].
    :param request: request
    :param path: редирект URL источника запроса
    :return: response.

    """
    if is_customer(request.user):
        cart = get_current_cart(request).get('cart')
        merge_anon_cart_with_user_cart(request, cart)
        if request.COOKIES.get('cart'):
            response = HttpResponseRedirect(path)
            response.delete_cookie('cart')
            response.delete_cookie('has_cart')
            return response
        return HttpResponseRedirect(path)
    return HttpResponseRedirect(path)
