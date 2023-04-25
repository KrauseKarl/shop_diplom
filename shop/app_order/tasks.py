import json
import time
from time import sleep

from celery import Celery
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.shortcuts import redirect

from app_cart.models import Cart
from app_cart.services.cart_services import get_current_cart, create_cart_item, create_session_key, set_cart_cookies
from app_item.models import Item
from app_item.services.item_services import ItemHandler
from app_order.services.order_services import Payment
from app_store.models import Store
from shop.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from app_order.models import Order
from app_invoice.models import Invoice
from app_settings.models import SiteSettings
from celery import shared_task
from celery_app import app


@shared_task
def pay_order(order_id, number, pay):
    sleep(2)

    if number % 2 != 0 or number % 10 == 0:
        error = Payment.error_generator()
        order = Order.objects.get(id=order_id)
        order.error = error
        order.save()
        return "error"
    else:
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            order.status = 'paid'
            order.is_paid = True
            if pay and pay != order.pay:
                order.pay = pay
            order.order_items.update(status='in_progress')
            if order.error:
                order.error = ''
            order.save()
            with transaction.atomic():
                Invoice.objects.create(
                    order=order,
                    number=number,
                    total_purchase_sum=order.total_sum - order.delivery_fees,
                    delivery_cost=order.delivery_fees,
                    total_sum=order.total_sum
                )
        # with transaction.atomic():
        #     for product in order.items_is_paid.all():
        #         item = Item.objects.get(cart_item=product.id)
        #         item.stock -= product.quantity
        #         item.save()

        return True



@app.task
def order_is_preparing(order_id):
    sleep(10)
    order = Order.objects.get(id=order_id)
    order.status = 'is_preparing'
    order.save()
    delivery_in_progress.delay(order_id)
    return True


@app.task
def delivery_in_progress(order_id):
    timer = SiteSettings().cache_detail_view
    sleep(10)
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'on_the_way'
        order.save()
        sleep(90)
        order.status = 'is_ready'
        order.save()
        return True
    except ObjectDoesNotExist:
        return False
