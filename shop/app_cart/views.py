from collections import Counter

from celery import Celery
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView, UpdateView, DetailView, CreateView

from app_cart.context_processors import get_cart
from app_cart.forms import AmountForm
from app_cart.models import Cart, CartItem
from app_cart.services.cart_services import *
from shop.settings import CELERY_RESULT_BACKEND, CELERY_BROKER_URL
app = Celery('tasks', backend=CELERY_RESULT_BACKEND, broker=CELERY_BROKER_URL)


class AddItemToCart(CreateView):
    """Класс-представление для добавления товара в корзину."""
    model = Cart
    template_name = 'app_item/item_detail.html'
    form_class = AmountForm

    def get(self, request, *args, **kwargs):
        item_id = kwargs['pk']
        path = add_item_in_cart(request, item_id)
        return path

    def post(self, request, *args, **kwargs):
        form = AmountForm(request.POST)
        item_id = kwargs['pk']
        if form.is_valid():
            quantity = form.cleaned_data.get('quantity')
            update = form.cleaned_data.get('update')
            path = add_item_in_cart(request, item_id, quantity)

            return path

    def form_invalid(self, form):
        return super().form_invalid(form)


class RemoveItemFromCart(TemplateView):
    """Класс-представление для удаление товара из корзины."""

    def get(self, request, *args, **kwargs):
        item_id = kwargs['pk']
        remove_from_cart(request, item_id)
        path = request.META.get('HTTP_REFERER')
        return redirect(path)


class UpdateCountItemFromCart(UpdateView):
    """Класс-представление для обновление кол-ва товара в корзине. """
    model = Cart
    template_name = 'app_cart/cart.html'
    context_object_name = 'cart'
    form_class = AmountForm

    def post(self, request, *args, **kwargs):
        form = AmountForm(request.POST)

        if form.is_valid():
            quantity = form.cleaned_data.get('quantity')
            update = form.cleaned_data.get('update')
            update_quantity_item_in_cart(request, quantity, update, **kwargs)
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)

    def form_invalid(self, form):
        return super().form_invalid(form)


class CartDetail(DetailView):
    """Класс-представление для отображение корзины."""
    model = Cart
    template_name = 'app_cart/cart.html'
    context_object_name = 'cart'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curr_cart'] = get_cart(self.request)
        total_lis = get_cart(self.request).get('cart_dict').get('book').values()
        context['total_amount_sum'] = sum(Counter([d['total'] for d in total_lis]).keys())
        print('00000 = ', context['total_amount_sum'])
        return context


class CreateCart(TemplateView):
    model = Cart
    template_name = 'app_cart/cart_detail.html'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        cart = create_cart(request)
        return cart
