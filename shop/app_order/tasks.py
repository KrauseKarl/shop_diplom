import json
import time
from time import sleep

from celery import Celery
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect

from app_cart.models import Cart
from app_cart.services.cart_services import get_current_cart, create_cart_item, create_session_key, set_cart_cookies
from app_item.models import Item
from app_item.services.item_services import ItemHandler
from app_order.services.order_services import Payment
from app_store.models import Store
from shop.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from app_order.models import Order, Invoice
from shop.celery import app


@app.task
def pay_order(order_id, number):
    sleep(10)
    if number % 2 != 0:
        error = Payment.error_generator()
        order = Order.objects.get(id=order_id)
        order.error = error
        order.save()
        return "error"
    else:
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            store = Store.objects.get(orders=order)
            order.status = 'in_progress'
            order.is_paid = True
            if order.error:
                order.error = ''
            order.save()
        with transaction.atomic():
            for product in order.items_is_paid.all():
                item = Item.objects.get(cart_item=product.id)
                item.stock -= product.quantity
                item.save()
        with transaction.atomic():
            Invoice.objects.create(
                order=order,
                number=number,
                recipient=store,
            )
        return True
    # return redirect('app_order:success_pay')
