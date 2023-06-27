import random

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect

# models
from app_cart import models as cart_models
from app_invoice import models as invoice_models
from app_item import models as item_models
from app_order import models as order_models
from app_settings import models as settings_models
from app_store import models as store_models

# services
from app_cart.services import cart_services
from app_user.services import register_services

# other
from app_cart.context_processors import get_cart


class CustomerOrderHandler:

    @staticmethod
    def create_order(request, form):
        """Функция содает заказ."""
        cart = cart_services.get_current_cart(request).get('cart')
        user = request.user
        post_address = form.cleaned_data.get('post_address')
        city = form.cleaned_data.get('city')
        address = form.cleaned_data.get('address')
        if len(post_address) < 1:
            AddressHandler.get_post_address(request, city, address)
        delivery_express_cost = CustomerOrderHandler.calculate_express_delivery_fees(form.cleaned_data.get('delivery'))
        delivery_cost = cart.is_free_delivery
        with transaction.atomic():
            stores = get_cart(request).get('cart_dict').get('book')
            order = order_models.Order.objects.create(
                user=user,
                name=form.cleaned_data.get('name'),
                email=form.cleaned_data.get('email'),
                telephone=register_services.ProfileHandler.telephone_formatter(form.cleaned_data.get('telephone')),
                delivery=form.cleaned_data.get('delivery'),
                pay=form.cleaned_data.get('pay'),
                city=city,
                address=address,
                total_sum=form.cleaned_data.get('total_sum'),
                delivery_fees=delivery_cost + delivery_express_cost,
                comment=form.cleaned_data.get('comment'),
            )
            for store_title, values in stores.items():
                store = store_models.Store.objects.get(title=store_title)
                order.store.add(store)
                order.save()

            cart_items = cart.items.filter(is_paid=False)
            with transaction.atomic():
                for cart_item in cart_items:
                    cart_item.is_paid = True
                    cart_item.save()
                    order_models.OrderItem.objects.create(
                        item=cart_item,
                        quantity=cart_item.quantity,
                        price=cart_item.price,
                        order=order,
                    )
                    cart_item.order = order
                    cart_item.status = 'not_paid'
                # product = Item.objects.get(id=cart_item.item.id)
                # product.stock -= cart_item.quantity
                # product.save()
                cart_services.delete_cart_cache(request)
                cart.is_archived = True
                cart.save()
        return order

    @staticmethod
    def get_customer_one_order(request):
        """Функция для получения списка всех заказов начиная с последнего."""
        try:
            return order_models.Order.objects.select_related('user').\
                filter(user_id=request.user.id).\
                order_by('-created')
        except ObjectDoesNotExist:
            raise Http404("Заказ не найден")

    @staticmethod
    def get_customer_order_list(request, delivery_status=None):
        try:
            if delivery_status:
                orders = order_models.Order.objects.filter(user=request.user).\
                    filter(status=delivery_status).\
                    order_by('-updated')
            else:
                orders = order_models.Order.objects.filter(user=request.user).order_by('-updated')
            return orders
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_last_customer_order(user):
        """Функция возвращает самый последний заказ пользователя."""
        try:
            last_order = order_models.Order.objects.filter(user=user).last()
        except ObjectDoesNotExist:
            last_order = None
        return last_order

    @staticmethod
    def calculate_express_delivery_fees(delivery):
        if delivery == 'express':
            res = settings_models.SiteSettings().express_delivery_price
            return res
        return 0

    @staticmethod
    def get_order_items(order):
        try:
            return order_models.OrderItem.objects.filter(order=order).order_by('item__store')
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_order(order_id):
        try:
            return order_models.Order.objects.filter(id=order_id).first()
        except ObjectDoesNotExist:
            return Http404('Такого заказ нет')


class SellerOrderHAndler:

    @staticmethod
    def get_seller_order_list(request):
        # собственник
        owner = request.user
        # все магазины собственника
        stores = store_models.Store.objects.select_related('owner').filter(owner=owner)
        # все товары в магазинах собственника
        items = item_models.Item.objects.select_related('store').filter(store__in=stores)

        # все заказанные товары из магазинов
        items_in_cart = cart_models.CartItem.objects.select_related('item').filter(item_id__in=items)
        order_items = order_models.OrderItem.objects.filter(item__in=items_in_cart)
        # # all sold product
        # items_my_store = items.filter(cart_item__in=items_in_cart)
        # все заказы в магазинах собственника
        # order_list = OrderItem.objects.select_related('user').prefetch_related('store'). \
        #     filter(order_items__in=items_in_cart). \
        #     order_by('-created')
        return order_items

    @staticmethod
    def get_seller_comment_list(request):
        # собственник
        owner = request.user
        # все магазины собственника
        stores = store_models.Store.objects.select_related('owner').filter(owner=owner)
        # все товары в магазинах собственника
        items = item_models.Item.objects.select_related('store').filter(store__in=stores)
        # все комментарии о товарах в магазинах собственника
        comment_list = item_models.Comment.objects.select_related('item').filter(item__in=items)
        if request.GET.get('is_published'):
            is_published = request.GET.get('is_published')
            comment_list = comment_list.filter(is_published=is_published, archived=False)
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

    @staticmethod
    def update_item_in_order(request, form):
        order_item = form.save()
        order_item.quantity = form.cleaned_data.get('quantity')
        order_item.total = order_item.item.price * form.cleaned_data.get('quantity')
        order_item.save()
        order_id = order_item.order.id
        order = order_models.Order.objects.get(id=order_id)
        store = order.store.first()
        new_total_order = 0
        for order_item in order.order_items.all():
            if order_item.total > store.min_for_discount:
                new_total_order += round(float(order_item.total) * ((100 - store.discount) / 100), 0)
            else:
                new_total_order += float(order_item.total)
        min_free_delivery = settings_models.SiteSettings().min_free_delivery
        delivery_fees = settings_models.SiteSettings().delivery_fees
        express_delivery_fees = settings_models.SiteSettings().express_delivery_price
        if new_total_order < min_free_delivery:
            new_delivery_fees = delivery_fees
        else:
            new_delivery_fees = 0
        if order.delivery == 'express':
            new_delivery_fees += express_delivery_fees
        order.total_sum = new_total_order + new_delivery_fees
        order.delivery_fees = new_delivery_fees
        order.save()
        return order


class Payment:
    ERROR_DICT = {
        '1': 'Оплата не выполнена, т.к. способствует вымиранию юго-восточных туканов',
        '2': 'Оплата не выполнена, т.к. способствует глобальному потеплению',
        '3': 'Оплата не выполнена, т.к. заблокирована мировым правительством',
        '4': 'Оплата не выполнена, т.к. была произведена не по  фэншую',
        '5': 'Оплата не выполнена, т.к. ретроградный Меркурий был в созведии Козерога',
    }

    @classmethod
    def get_invoice(cls, invoice_id):
        """Возвращает экземпляр квитанции по ID."""
        try:
            invoice = invoice_models.Invoice.objects.get(id=invoice_id)
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
        post_address, created = order_models.Address.objects.get_or_create(
            city=city,
            address=address,
            user=request.user
        )
        return post_address

    @staticmethod
    def get_address_list(request):
        try:
            user = request.user
            return order_models.Address.objects.filter(user=user)
        except ObjectDoesNotExist:
            return []

    @staticmethod
    def delete_address(request, address_id):
        address = order_models.Address.objects.get(id=address_id)
        user = request.user
        if address in user.address.all():
            address.delete()


class AdminOrderHAndler:
    @staticmethod
    def orders():
        return order_models.Order.objects.all()
