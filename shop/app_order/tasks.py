from time import sleep

from celery import Celery
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import transaction, IntegrityError
from django.db.models import Sum
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
            order.status = 'paid'
            order.is_paid = True

            if pay and pay != order.pay:
                order.pay = pay
            order.order_items.update(status='paid')

            if order.error:
                order.error = ''
            order.save()

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
                item.save(update_fields=['stock'])

        return True