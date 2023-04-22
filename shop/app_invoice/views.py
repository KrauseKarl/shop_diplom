from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import render
from django.views import generic

from app_invoice.models import Invoice
from app_order.models import Order
from utils.my_utils import MixinPaginator, CustomerOnlyMixin


class InvoicesList(CustomerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представления для получения списка всех квитанций об оплате."""
    model = Invoice
    template_name = 'app_invoice/invoices_list.html'
    context_object_name = 'invoices'
    paginate_by = 3

    def get(self, request, sort=None, **kwargs):
        super().get(request, **kwargs)
        orders = Order.objects.filter(user=self.request.user)
        invoices = Invoice.objects.filter(order__in=orders)
        if sort:
            invoices = invoices.order_by(f'{sort}')
        queryset = self.my_paginator(invoices, self.request, self.paginate_by)
        context = {
            'object_list': queryset
        }
        return render(request, self.template_name, context=context)


class InvoicesDetail(UserPassesTestMixin, generic.DetailView):
    model = Invoice
    template_name = 'app_invoice/invoice_detail.html'
    context_object_name = 'invoice'

    def test_func(self):
        invoice = self.get_object()
        if self.request.user.id == invoice.order.user.id:
            return True
        return False
