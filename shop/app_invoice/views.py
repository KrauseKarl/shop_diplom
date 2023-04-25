from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import render
from django.views import generic

from app_invoice import models as invoice_models
from app_order.services import order_services
from utils.my_utils import MixinPaginator, CustomerOnlyMixin


class InvoicesList(CustomerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представления для получения списка всех квитанций об оплате."""
    model = invoice_models.Invoice
    template_name = 'app_invoice/invoices_list.html'
    context_object_name = 'invoices'
    paginate_by = 3

    def get(self, request, sort=None, **kwargs):
        super().get(request, **kwargs)
        orders = order_services.CustomerOrderHandler.get_customer_order_list(request)
        queryset = invoice_models.Invoice.objects.filter(order__in=orders)
        if sort:
            queryset = queryset.order_by(f'{sort}')
        object_list = MixinPaginator(queryset, request, self.paginate_by).my_paginator()
        context = {'object_list': object_list}
        return render(request, self.template_name, context=context)


class InvoicesDetail(UserPassesTestMixin, generic.DetailView):
    model = invoice_models.Invoice
    template_name = 'app_invoice/invoice_detail.html'
    context_object_name = 'invoice'

    def test_func(self):
        invoice = self.get_object()
        if self.request.user.id == invoice.order.user.id:
            return True
        return False
