from time import sleep

from celery import Celery
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import transaction, IntegrityError
from django.db.models import Sum, F
from django.shortcuts import redirect

# models
from app_order import models as order_models
from app_invoice import models as invoice_models
from app_item import models as item_models
# services
from app_order.services import order_services
# others
from shop.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from celery import shared_task
from shop.celery import app


@shared_task
def paying(order_id, number, pay):
    sleep(2)
    if number % 2 != 0 or number % 10 == 0:
        error = order_services.Payment.error_generator()
        order = order_models.Order.objects.get(id=order_id)
        order.error = error
        order.save()
        return "error"
    else:
        with transaction.atomic():
            order = order_models.Order.objects.get(id=order_id)
            if pay and pay != order.pay:
                order.pay = pay
            order.status = 'paid'
            order.is_paid = True
            order.order_items.update(is_paid=True)
            order.order_items.update(status='paid')

            if order.error:
                order.error = ''
            order.save(update_fields=['pay', 'status', 'error', 'is_paid'])

            with transaction.atomic():
                invoice_models.Invoice.objects.create(
                    order=order,
                    number=number,
                    total_purchase_sum=order.total_sum - order.delivery_fees,
                    delivery_cost=order.delivery_fees,
                    total_sum=order.total_sum
                )
        with transaction.atomic():
            for order_item in order.order_items.all():
                item = item_models.Item.objects.get(cart_item=order_item.item)
                item.stock -= order_item.quantity
                item.save()

        return True


@app.task
def check_order_status(order_id):
    sleep(3)
    try:
        order = order_models.Order.objects.get(id=order_id)

        has_sent = 0

        for order_item in order.order_items.all():
            if order_item.status == 'on_the_way':
                has_sent += 1

        if has_sent == order.order_items.count():
            order.status = 'on_the_way'
            order.save(update_fields=['status'])
            sleep(5)
            order.status = 'is_ready'
            order.order_items.update(status='is_ready')
            order.save(update_fields=['status'])
        else:
            order.status = 'is_preparing'
            order.save(update_fields=['status'])
        return True
    except ObjectDoesNotExist:
        return False
