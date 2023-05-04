from collections import Counter

from celery import Celery
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.db import connection
from django.shortcuts import redirect
from django.views import generic

from app_cart.context_processors import get_cart
from app_cart.forms import AmountForm
from app_cart.models import Cart, CartItem
from app_cart.services import cart_services
from shop.settings import CELERY_RESULT_BACKEND, CELERY_BROKER_URL
from utils.my_utils import CustomerOnlyMixin

app = Celery('tasks', backend=CELERY_RESULT_BACKEND, broker=CELERY_BROKER_URL)


class AddItemToCart(generic.CreateView):
    """Класс-представление для добавления товара в корзину."""
    model = Cart
    template_name = 'app_item/item_detail.html'
    form_class = AmountForm

    def get(self, request, *args, **kwargs):
        item_id = kwargs['pk']
        path = cart_services.add_item_in_cart(request, item_id)
        return path

    def post(self, request, *args, **kwargs):
        form = AmountForm(request.POST)
        item_id = kwargs['pk']
        if form.is_valid():
            quantity = form.cleaned_data.get('quantity')
            update = form.cleaned_data.get('update')
            print('++++++++++++++++++++++++++++++++',quantity)
            path = cart_services.add_item_in_cart(request, item_id, quantity)

            return path

    def form_invalid(self, form):
        return super().form_invalid(form)


class RemoveItemFromCart(generic.TemplateView):
    """Класс-представление для удаление товара из корзины."""

    def get(self, request, *args, **kwargs):
        item_id = kwargs['pk']
        cart_services.remove_from_cart(request, item_id)
        path = request.META.get('HTTP_REFERER')
        return redirect(path)


class UpdateCountItemFromCart(generic.UpdateView):
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
            cart_services.update_quantity_item_in_cart(request, quantity, update, **kwargs)
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)

    def form_invalid(self, form):
        return super().form_invalid(form)


class CartDetail(generic.DetailView):
    """Класс-представление для отображение корзины."""
    model = Cart
    template_name = 'app_cart/cart.html'
    context_object_name = 'cart'

    # def test_func(self):
    #     cart = self.get_object()
    #     if self.request.user.id == cart.user.id:
    #         return True
    #     return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curr_cart'] = get_cart(self.request)
        total_lis = get_cart(self.request).get('cart_dict').get('book').values()
        context['total_amount_sum'] = sum(Counter([d['total'] for d in total_lis]).keys())
        print('\nЗАПРОСЫ = ', len(connection.queries))
        return context


class CreateCart(generic.TemplateView):
    model = Cart
    template_name = 'app_cart/cart_detail.html'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        cart = cart_services.create_cart(request)
        return cart
