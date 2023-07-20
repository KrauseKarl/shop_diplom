"""Модуль содержит классы-предстывления для работы с корзиной."""
from collections import Counter
from celery import Celery
from django.shortcuts import redirect
from django.views import generic

# models
from app_cart import models as cart_models

# forms
from app_cart import forms as cart_forms

# services
from app_cart.services import cart_services

# other
from app_cart.context_processors import get_cart
from shop import settings

app = Celery(
    "tasks",
    backend=settings.CELERY_RESULT_BACKEND,
    broker=settings.CELERY_BROKER_URL,
)


class AddItemToCart(generic.CreateView):
    """Класс-представление для добавления товара в корзину."""

    model = cart_models.Cart
    template_name = "app_item/item_detail.html"
    form_class = cart_forms.AmountForm

    def get(self, request, *args, **kwargs):
        """GET-функция добавляет товар в корзину."""
        item_id = kwargs["pk"]
        path = cart_services.add_item_in_cart(request, item_id)
        return path

    def post(self, request, *args, **kwargs):
        """POST-функция добавляет несколько единиц товара в корзину."""
        form = cart_forms.AmountForm(request.POST)
        item_id = kwargs["pk"]
        if form.is_valid():
            quantity = form.cleaned_data.get("quantity")
            path = cart_services.add_item_in_cart(request, item_id, quantity)
            return path

    def form_invalid(self, form):
        return super().form_invalid(form)


class RemoveItemFromCart(generic.TemplateView):
    """Класс-представление для удаление товара из корзины."""

    def get(self, request, *args, **kwargs):
        """GET-функция удаляет товар из корзины."""
        item_id = kwargs["pk"]
        cart_services.remove_from_cart(request, item_id)
        path = request.META.get("HTTP_REFERER")
        return redirect(path)


class UpdateCountItem(generic.UpdateView):
    """Класс-представление для обновление кол-ва товара в корзине."""

    model = cart_models.Cart
    template_name = "app_cart/cart.html"
    context_object_name = "cart"
    form_class = cart_forms.AmountForm

    def post(self, request, *args, **kwargs):
        """POST-функция обновляет кол-во товара в корзине."""
        form = cart_forms.AmountForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data.get("quantity")
            update = form.cleaned_data.get("update")
            cart_services.update_quantity_item_in_cart(
                request, quantity, update, **kwargs
            )
            path = self.request.META.get("HTTP_REFERER")
            return redirect(path)


class CartDetail(generic.DetailView):
    """Класс-представление для отображение корзины."""

    model = cart_models.Cart
    template_name = "app_cart/cart.html"
    context_object_name = "cart"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart"] = get_cart(self.request).get("cart_dict").get("cart")
        context["not_enough"] = cart_services.enough_checker(context["cart"])
        try:
            total_list = (
                get_cart(self.request).get("cart_dict").get("book").values()
            )

            context["total_amount_sum"] = sum(
                Counter([d["total"] for d in total_list]).keys()
            )
        except AttributeError:
            context["total_amount_sum"] = 0
        return context


class CreateCart(generic.TemplateView):
    """Класс-представление для создания корзины."""

    model = cart_models.Cart
    template_name = "app_cart/cart_detail.html"

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        cart = cart_services.create_cart(request)
        return cart
