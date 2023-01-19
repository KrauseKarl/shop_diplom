import random

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect
from app_cart.models import Cart
from app_item.services.item_services import ItemHandler
from app_order.models import Order, Invoice


def get_order(user):
    """Функция для получения списка всех заказов начиная с последнего."""
    try:
        return Order.objects.select_related('user').filter(user_id=user.id).order_by('-created')
    except ObjectDoesNotExist:
        raise Http404("Заказ не найден")


def get_last_user_order(user):
    """Функция возвращает самый последний заказ пользователя."""
    try:
        last_order = Order.objects.filter(user=user).last()
    except ObjectDoesNotExist:
        last_order = None
    return last_order


class Payment:
    payment_array = []  # list-очередь
    error_list = [
        'error_1',
        'error_2',
        'error_3'
    ]  # list-error

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
    def add_order_to_job(cls, invoice_id):
        """Добавляет экземпляр квитанции в очередь на оплату."""
        invoice = Payment.get_invoice(invoice_id)
        if invoice not in cls.payment_array:
            cls.payment_array.append(invoice)
        return invoice

    @classmethod
    def error_generator(cls):
        """Генерирует случайную ошибку."""
        index = random.randint(0, 2)
        return cls.error_list[index]

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
