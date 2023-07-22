"""
Модуль содержит сервисы работы с заказами, оплатой, и адресами.

#1 AdminOrderHAndler - класс для работы с заказами со стороны администратора.
#2 CustomerOrderHandler - класс для работы с заказами со стороны покупателя.
#3 SellerOrderHAndler - класс для работы с заказами со стороны продавца.
#4 Payment - класс для работы с оплатойзаказа.
#5 AddressHandler - класс для работы с адресами доставки покупателя.
"""
import random

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404

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


class AdminOrderHAndler:
    """Класс для работы с заказами со стороны администратора."""

    @staticmethod
    def orders_count() -> int:
        """Фнкция возвращает кол-во заказов в БД."""
        return order_models.Order.objects.count()

    @staticmethod
    def get_all_order():
        """Фнкция возвращает список заказов из БД."""
        return order_models.Order.objects.all()


class CustomerOrderHandler:
    """Класс для работы с заказами со стороны покупателя."""

    @staticmethod
    def create_order(request, form):
        """Функция содает заказ."""
        cart = cart_services.get_current_cart(request).get("cart")
        user = request.user
        post_address = form.cleaned_data.get("post_address")
        city = form.cleaned_data.get("city")
        address = form.cleaned_data.get("address")
        if len(post_address) < 1:
            AddressHandler.create_post_address(
                user=request.user, city=city, address=address
            )
        print(form.cleaned_data.get("delivery"))
        delivery_express_cost = (
            CustomerOrderHandler.calculate_express_delivery_fees(
                form.cleaned_data.get("delivery")
            )
        )
        delivery_cost = cart.is_free_delivery
        with transaction.atomic():
            stores = get_cart(request).get("cart_dict").get("book")
            order = order_models.Order.objects.create(
                user=user,
                name=form.cleaned_data.get("name"),
                email=form.cleaned_data.get("email"),
                telephone=register_services.ProfileHandler.telephone_formatter(
                    form.cleaned_data.get("telephone")
                ),
                delivery=form.cleaned_data.get("delivery"),
                pay=form.cleaned_data.get("pay"),
                city=city,
                address=address,
                total_sum=form.cleaned_data.get("total_sum"),
                delivery_fees=delivery_cost + delivery_express_cost,
                comment=form.cleaned_data.get("comment"),
            )
            for store_title, values in stores.items():
                store = store_models.Store.objects.get(title=store_title)
                order.store.add(store)
                order.save()

            cart_items = cart.all_items.filter(is_paid=False)
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
                    cart_item.status = "not_paid"

                cart.is_archived = True
                cart.save()
        return order

    @staticmethod
    def get_customer_order_list(user, delivery_status=None) -> QuerySet:
        """
        Функция возвращает список заказов пользователя.

        :param user: пользователь
        :param delivery_status: статус заказа
        :return: queryset заказов
        """
        try:
            if delivery_status:
                orders = (
                    order_models.Order.objects.filter(user=user)
                    .filter(status=delivery_status)
                    .order_by("-updated")
                )
            else:
                orders = order_models.Order.objects.filter(user=user).order_by(
                    "-updated"
                )
            return orders
        except ObjectDoesNotExist:
            raise Http404("Заказов нет")

    @staticmethod
    def get_last_customer_order(user):
        """Функция возвращает самый последний заказ пользователя."""
        try:
            return order_models.Order.objects.filter(user=user).last()
        except ObjectDoesNotExist:
            raise Http404("Заказов нет")

    @staticmethod
    def get_order(order_id):
        """Функция возвращает один заказ пользователя по ID."""
        try:
            return order_models.Order.objects.filter(id=order_id).first()
        except ObjectDoesNotExist:
            return Http404("Такого заказ нет")

    @staticmethod
    def calculate_express_delivery_fees(delivery):
        """Функция возвращает стоимость ЭКСПРЕСС доставки заказа."""
        if delivery == "express":
            return settings_models.SiteSettings.objects.get(
                id=1
            ).express_delivery_price
        return 0

    @staticmethod
    def get_order_items(order):
        """Функция возвращает все товары в заказе."""
        try:
            return order_models.OrderItem.objects.filter(order=order).order_by(
                "item__store"
            )
        except ObjectDoesNotExist:
            return Http404("Товаров нет")


class SellerOrderHAndler:
    """Класс для работы с заказами со стороны продавца."""

    @staticmethod
    def get_seller_order_list(owner):
        """Функция возвращает список всех заказов продавца."""
        # все магазины собственника
        stores = store_models.Store.objects.select_related("owner").filter(
            owner=owner
        )
        # все товары в магазинах собственника
        items = item_models.Item.objects.select_related("store").filter(
            store__in=stores
        )
        # все заказанные товары из магазинов
        items_in_cart = cart_models.CartItem.objects.select_related(
            "item"
        ).filter(item_id__in=items)
        order_items = order_models.Order.objects.filter(
            store__in=stores
        ).order_by("-created")

        return order_items

    @staticmethod
    def get_seller_comment_list(user, param: dict) -> QuerySet:
        """Функция возвращает список всех комментариев к товарам продавца."""
        # собственник
        # все магазины собственника
        stores = store_models.Store.objects.select_related("owner").filter(
            owner=user
        )
        # все товары в магазинах собственника
        items = item_models.Item.objects.select_related("store").filter(
            store__in=stores
        )
        # все комментарии о товарах в магазинах собственника
        comment_list = item_models.Comment.objects.select_related(
            "item"
        ).filter(item__in=items)
        if param.get("is_published"):
            is_published = param.get("is_published")
            comment_list = comment_list.filter(
                is_published=is_published, archived=False
            )
        return comment_list

    @staticmethod
    def get_seller_comment_amount(request):
        """Функция возвращает колчество всех новых комментариев."""
        comments = SellerOrderHAndler.get_seller_comment_list(
            user=request.user, param=request.GET
        )
        comment_amount = comments.filter(is_published=False).count()
        return comment_amount

    @staticmethod
    def get_order_total_amount(user_id: int) -> int:
        """
        Функция возвращает общее кол-во заказов.

        Общее кол-во заказов со статусами "Новый"
        в магазине продавца
        :param user_id: ID пользователя
        :return: кол-во заказов
        """
        paid_order = order_models.Order().STATUS[1][0]

        order_list = SellerOrderHAndler.get_seller_order_list(owner=user_id)
        # кол-во всех заказов со статусами ('new')
        order_total_amount = (
            order_list.values_list("status").filter(status=paid_order).count()
        )

        return order_total_amount

    @staticmethod
    def update_item_in_order(request, form):
        """
        Функция редактирует информацию о заказе.

        Пересчитывает его общюю стоимсоть,
        стоимость доставки в магазине продавца.
        """
        order_item = form.save()
        order_item.quantity = form.cleaned_data.get("quantity")
        order_item.total = order_item.item.price * form.cleaned_data.get(
            "quantity"
        )
        order_item.save()
        order_id = order_item.order.id
        order = order_models.Order.objects.get(id=order_id)
        store = order.store.first()
        new_total_order = 0
        for order_item in order.order_items.all():
            if order_item.total > store.min_for_discount:
                new_total_order += round(
                    float(order_item.total) * ((100 - store.discount) / 100), 0
                )
            else:
                new_total_order += float(order_item.total)
        min_free_delivery = settings_models.SiteSettings().min_free_delivery
        delivery_fees = settings_models.SiteSettings().delivery_fees
        express_delivery_fees = (
            settings_models.SiteSettings().express_delivery_price
        )
        if new_total_order < min_free_delivery:
            new_delivery_fees = delivery_fees
        else:
            new_delivery_fees = 0
        if order.delivery == "express":
            new_delivery_fees += express_delivery_fees
        order.total_sum = new_total_order + new_delivery_fees
        order.delivery_fees = new_delivery_fees
        order.save()
        return order

    @staticmethod
    def sent_item(order_id: int, status: str):
        """Функция отправляет заказ. Статус 'доставляется'."""
        order_item = order_models.OrderItem.objects.get(id=order_id)
        order_item.status = status
        order_item.save(update_fields=["status"])
        return order_item


class Payment:
    """Класс для работы с оплатойзаказа."""

    ERROR_DICT = {
        "1": "Оплата не выполнена, т.к. способствует вымиранию туканов",
        "2": "Оплата не выполнена, т.к. способствует глобальному потеплению",
        "3": "Оплата не выполнена, т.к. заблокирована мировым правительством",
        "4": "Оплата не выполнена, т.к. была произведена не по фэншую",
        "5": "Оплата не выполнена, т.к. ретроградный Меркурий был в созведии Рыбы",
    }

    @staticmethod
    def get_invoice(invoice_id):
        """Возвращает экземпляр квитанции по ID."""
        try:
            invoice = invoice_models.Invoice.objects.get(id=invoice_id)
            return invoice
        except ObjectDoesNotExist:
            raise Http404("Квитанция не найдена")

    @staticmethod
    def get_invoice_status(invoice_id):
        """Возвращает статус заказа."""
        invoice = Payment.get_invoice(invoice_id)
        return invoice.order.status

    @staticmethod
    def error_generator():
        """Генерирует случайную ошибку."""
        index = str(random.randint(1, len(Payment.ERROR_DICT)))
        error = Payment.ERROR_DICT[index]
        return error


class AddressHandler:
    """Класс для работы с адресами доставки покупателя."""

    @staticmethod
    def create_post_address(user, city: str, address: str):
        """Функция создает новый адрес доставки."""
        post_address, created = order_models.Address.objects.get_or_create(
            city=city, address=address, user=user
        )
        return post_address

    @staticmethod
    def get_address_list(user):
        """Функция список всех адресов доставки покупателя."""
        try:
            return order_models.Address.objects.filter(user=user)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def delete_address(user, address_id: int):
        """Функция удаляет адрес доставки покупателя."""
        address = order_models.Address.objects.get(id=address_id)
        if address in user.address.all():
            address.delete()
