from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django import forms
from django.core import serializers
from django.http import HttpResponse
from django.http.response import HttpResponseBase, JsonResponse

from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.views.decorators import csrf
from django.views.generic import TemplateView, ListView, UpdateView, DetailView, FormView, CreateView

from app_cart.context_processors import get_cart
from app_cart.forms import AmountForm
from app_cart.models import Cart, CartItem
from app_cart.services.cart_services import add_item_in_cart, update_quantity_item_in_cart, remove_from_cart, \
    create_cart
from app_item.services.item_services import ItemHandler
from app_user.models import Profile
from app_user.services.user_services import get_user


class AddItemToCart(TemplateView):
    """Класс-представление для добавления товара в корзину."""
    model = Cart
    template_name = 'app_item/item_detail.html'

    def get(self, request, *args, **kwargs):
        item_id = kwargs['pk']
        path = add_item_in_cart(request, item_id)
        return path


class RemoveItemFromCart(TemplateView):
    """Класс-представление для удаление товара из корзины."""

    def get(self, request, *args, **kwargs):
        item_id = kwargs['pk']
        remove_from_cart(request, item_id, **kwargs)
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
        return context


class CreateCart(TemplateView):
    model = Cart
    template_name = 'app_cart/cart_detail.html'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        cart = create_cart(request)
        return cart
