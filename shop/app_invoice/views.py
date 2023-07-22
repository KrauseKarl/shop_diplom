"""
Модуль содержит классы-предстывления для работы с квитанциями и адресами.

InvoicesList - класс-представление для получения список квитанций об оплате,
InvoicesDetail -  класс-представление для получения одна квитануия об оплате заказа,
AddressList - класс-представление для отображения списка адресов доставки,
AddressCreate - класс-представление для создания адреса доставки
AddressUpdate - класс-представление для создания адреса доставки
AddressDelete - класс-представление для обновления адреса доставки
"""
from django.contrib import messages
from django.contrib.auth import mixins
from django.shortcuts import render, redirect
from django.views import generic

# models
from app_invoice import models as invoice_models
from app_order import models as order_models

# forms
from app_invoice import forms as invoice_forms

# services
from app_order.services import order_services

# others
from utils.my_utils import MixinPaginator, CustomerOnlyMixin


# INVOICE
class InvoicesList(CustomerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для получения списка всех квитанций об оплате."""

    model = invoice_models.Invoice
    template_name = "app_invoice/invoice/invoices_list.html"
    context_object_name = "invoices"
    paginate_by = 3

    def get(self, request, sort=None, **kwargs):
        super().get(request, **kwargs)
        orders = order_services.CustomerOrderHandler.get_customer_order_list(
            request
        )
        queryset = invoice_models.Invoice.objects.filter(order__in=orders)
        if sort:
            queryset = queryset.order_by(f"{sort}")
        object_list = MixinPaginator(
            queryset, request, self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list}
        return render(request, self.template_name, context=context)


class InvoicesDetail(mixins.UserPassesTestMixin, generic.DetailView):
    """Класс-представление для отображения одной квитануии об оплате заказа."""

    model = invoice_models.Invoice
    template_name = "app_invoice/invoice/invoice_detail.html"
    context_object_name = "invoice"

    def test_func(self):
        invoice = self.get_object()
        if self.request.user.id == invoice.order.user.id:
            return True
        return False


# ADDRESS
class AddressList(mixins.LoginRequiredMixin, generic.ListView):
    """Класс-представление для отображения списка адресов доставки покупателя."""

    model = order_models.Address
    template_name = "app_invoice/address/address_list.html"
    context_object_name = "addresses"

    def get(self, request, *args, **kwargs):
        super(AddressList, self).get(request, *args, **kwargs)
        object_list = order_services.AddressHandler.get_address_list(
            self.request.user
        )
        form = invoice_forms.AddressForm
        context = {"form": form, "object_list": object_list}
        return render(request, self.template_name, context=context)


class AddressCreate(AddressList, generic.CreateView):
    """Класс-представление для создания адреса доставки."""

    model = order_models.Address
    form_class = invoice_forms.AddressForm
    template_name = "app_invoice/address/address_list.html"
    MESSAGE_SUCCESS = "Новый адрес доставки сохранен"
    MESSAGE_ERROR = "Ошибка сохранения адреса"

    def form_valid(self, form):
        address = form.save(commit=False)
        address.city = form.cleaned_data.get("city").title()
        address.address = form.cleaned_data.get("address")
        address.user = self.request.user
        address.save()
        messages.add_message(
            self.request, messages.SUCCESS, self.MESSAGE_SUCCESS
        )
        return redirect("app_invoice:address_list")

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, self.MESSAGE_ERROR)
        return super().form_invalid(form)


class AddressUpdate(CustomerOnlyMixin, AddressList, generic.UpdateView):
    """Класс-представление для обновления адреса доставки."""

    model = order_models.Address
    form_class = invoice_forms.AddressForm
    MESSAGE_SUCCESS = "Данные адреса доставки изменены"
    MESSAGE_ERROR = "Ошибка.Адрес не обновлен."

    def test_func(self):
        user = self.request.user
        address = self.get_object()
        return True if user == address.user else False

    def form_valid(self, form):
        form.save()
        messages.add_message(
            self.request, messages.SUCCESS, self.MESSAGE_SUCCESS
        )
        return redirect("app_invoice:address_list")

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, self.MESSAGE_ERROR)
        return super().form_invalid(form)


class AddressDelete(
    CustomerOnlyMixin, mixins.UserPassesTestMixin, generic.DeleteView
):
    """Класс-представления для удаления адреса доставки."""

    model = order_models.Address
    MESSAGE_SUCCESS = "Адрес успешно удален"

    def test_func(self):
        user = self.request.user
        address = self.get_object()
        return True if user == address.user else False

    def get(self, request, *args, **kwargs):
        address_id = kwargs["pk"]
        order_services.AddressHandler.delete_address(request.user, address_id)
        messages.add_message(self.request, messages.INFO, self.MESSAGE_SUCCESS)
        return redirect("app_invoice:address_list")
