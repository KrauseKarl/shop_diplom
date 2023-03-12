import random

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect
from app_cart.models import Cart, CartItem
from app_item.models import Item, Comment
from app_order.models import Order, Invoice, Address
from app_store.models import Store


class CustomerOrderHandler:

    @staticmethod
    def get_customer_one_order(request):
        """Функция для получения списка всех заказов начиная с последнего."""
        try:
            return Order.objects.select_related('user').filter(user_id=request.user.id).order_by('-created')
        except ObjectDoesNotExist:
            raise Http404("Заказ не найден")

    @staticmethod
    def get_customer_order_list(request, delivery_status=None):
        try:
            if delivery_status:
                orders = Order.objects.filter(user=request.user).filter(status=delivery_status).order_by('-created')
            else:
                orders = Order.objects.filter(user=request.user).order_by('-created')
            return orders
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_last_customer_order(user):
        """Функция возвращает самый последний заказ пользователя."""
        try:
            last_order = Order.objects.filter(user=user).last()
        except ObjectDoesNotExist:
            last_order = None
        return last_order


class SellerOrderHAndler:

    @staticmethod
    def get_seller_order_list(request):
        # собственник
        owner = request.user
        # все магазины собственника
        stores = Store.objects.select_related('owner').filter(owner=owner)
        # все товары в магазинах собственника
        items = Item.objects.select_related('store').filter(store__in=stores)

        # все заказанные товары из магазинов
        items_in_cart = CartItem.objects.select_related('item').filter(item_id__in=items)
        # # all sold product
        # items_my_store = items.filter(cart_item__in=items_in_cart)
        # все заказы в магазинах собственника
        order_list = Order.objects.select_related('user', 'store').\
            filter(items_is_paid__in=items_in_cart).\
            order_by('-created')
        return order_list

    @staticmethod
    def get_seller_comment_list(request):
        # собственник
        owner = request.user
        # все магазины собственника
        stores = Store.objects.select_related('owner').filter(owner=owner)
        # все товары в магазинах собственника
        items = Item.objects.select_related('store').filter(store__in=stores)
        # все комментарии о товарах в магазинах собственника
        comment_list = Comment.objects.select_related('item').filter(item__in=items)
        return comment_list

    @staticmethod
    def get_seller_comment_new_amount(request):
        comments = SellerOrderHAndler.get_seller_comment_list(request)
        new_comment_amount = comments.filter(is_published=False).count()
        return new_comment_amount

    @staticmethod
    def get_order_total_amount(request):
        """
        Функция возвращает общее кол-во заказов в магазине продавца
         со статусами "Новый"
        :param request: request
        :return: int()
        """
        order_list = SellerOrderHAndler.get_seller_order_list(request)
        # кол-во всех заказов со статусами ('new')
        order_total_amount = order_list.values_list('status').filter(status='new').count()

        return order_total_amount


class Payment:

    ERROR_DICT = {
        '1': 'способствует вымиранию юго-восточных туканов  ',
        '2': 'способствует глобальному потеплению',
        '3': 'заблокирована мировым правительством',
    }

    @classmethod
    def get_invoice(cls, invoice_id):
        """Возвращает экземпляр квитанции по ID."""
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            return invoice
        except ObjectDoesNotExist:
            raise Http404('Квитанция не найдена')

    @classmethod
    def get_invoice_status(cls, invoice_id):
        """Возвращает статус заказа."""
        invoice = Payment.get_invoice(invoice_id)
        return invoice.order.status

    @classmethod
    def error_generator(cls):
        """Генерирует случайную ошибку."""
        index = str(random.randint(1, len(cls.ERROR_DICT)))
        error = cls.ERROR_DICT[index]
        return error

    @classmethod
    def init_payment(cls):
        """Инициирует оплату заказа."""
        last_invoice = cls.payment_array.pop()
        card_number = last_invoice.number
        last_card_number = int(card_number[-1])

        if last_card_number % 2 != 0 or last_card_number != 0:
            last_invoice.order.is_paid = True
            last_invoice.order.save()
            cls.payment_array = cls.payment_array.remove(last_invoice)
            return redirect('app_order:success_pay')
        else:
            error = cls.error_generator()
            last_invoice.order.error = error
            last_invoice.order.save()
            return error


class AddressHandler:
    @staticmethod
    def get_post_address(request, city, address):
        post_address, created = Address.objects.get_or_create(
            city=city,
            address=address,
            user=request.user
        )
        return post_address

    @staticmethod
    def get_address_list(request):
        try:
            user = request.user
            return Address.objects.filter(user=user)
        except ObjectDoesNotExist:
            return []

    @staticmethod
    def delete_address(request, address_id):
        address = Address.objects.get(id=address_id)
        user = request.user
        if address in user.address.all():
            address.delete()