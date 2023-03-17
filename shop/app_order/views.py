from time import sleep

from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView, DeleteView

from app_cart.context_processors import get_cart
from app_cart.models import CartItem
from app_cart.services.cart_services import get_current_cart
from app_invoice.forms import PaymentForm
from app_item.models import Item
from app_settings.models import SiteSettings
from app_user.services.register_services import ProfileHandler
from utils.my_utils import MixinPaginator

from app_order.forms import OrderCreateForm, AddressForm
from app_order.models import Order, Address, OrderItem
from app_order.services.order_services import CustomerOrderHandler, AddressHandler, Payment
from app_store.form import UpdateOrderStatusForm
from app_store.models import Store
from app_order.models import Order
from app_order.tasks import pay_order


class OrderCreate(CreateView):
    model = Order
    form_class = OrderCreateForm
    extra_context = {'type_of_delivery': SiteSettings.DELIVERY, 'type_of_payment': SiteSettings.PAY_TYPE}

    def get_template_names(self):
        super(OrderCreate, self).get_template_names()
        templates_dict = {
            True: 'app_order/create_order_auth.html',
            False: 'app_order/create_order_anon.html'
        }
        user_role = self.request.user.is_authenticated
        name = templates_dict[user_role]
        return name

    def form_valid(self, form):
        CustomerOrderHandler.create_order(self.request, form)
        return redirect('app_order:success_order')

    def form_invalid(self, form):
        return render(self.request, 'app_order/failed_order.html', {'error': form.errors})


class SuccessOrdered(TemplateView):
    template_name = 'app_order/successful_order.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['order'] = Order.objects.filter(user=request.user).order_by('-id')
        return self.render_to_response(context)


class FailedOrdered(TemplateView):
    template_name = 'app_order/failed_order.html'


class OrderList(ListView, MixinPaginator):
    model = Order
    template_name = 'app_order/order_list.html'
    context_object_name = 'orders'
    paginate_by = 5
    extra_context = {}

    # permission_required = ('app_order.view_order', 'app_order.change_order')

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        if self.request.user.is_authenticated:
            delivery_status = self.request.GET.get('status')
            queryset = CustomerOrderHandler.get_customer_order_list(self.request, delivery_status)
            # queryset = CartItem.objects.filter(user=request.user)
            object_list = self.my_paginator(queryset, self.request, self.paginate_by)
            context = {'object_list': object_list, 'status_list': CartItem.STATUS}
            print(queryset)
        else:
            context = {'object_list': None, 'status_list': CartItem().STATUS}
        return render(request, self.template_name, context=context)


class OrderDetail(UserPassesTestMixin, DetailView):  # UserPassesTestMixin PermissionsMixin
    model = Order
    template_name = 'app_order/order_detail.html'
    context_object_name = 'order'

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        if user == order.user:
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = OrderItem.objects.filter(
            order=self.get_object()).order_by('item__store')  # TODO service def _get_has_paid_items
        return context


class OrderUpdatePayWay(UpdateView):
    model = Order
    template_name = 'app_order/order_update_pay_way.html'
    fields = ['pay']
    extra_context = {'type_of_payment': SiteSettings().PAY_TYPE}

    def get_success_url(self):
        return reverse('app_order:progress_payment', kwargs={'pk': self.object.pk})


class SuccessPaid(TemplateView):
    template_name = 'app_order/successful_pay.html'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        order = Order.objects.get(id=kwargs['order_id'])
        context['order'] = order
        context['invoice'] = order.invoices.first
        return self.render_to_response(context)


class FailedPaid(TemplateView):
    template_name = 'app_order/failed_pay.html'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        context['order'] = kwargs['order_id']
        order = Order.objects.get(id=kwargs['order_id'])
        context['error'] = order.error
        return self.render_to_response(context)


class PaymentView(DetailView, CreateView):
    model = Order
    form_class = PaymentForm
    template_name = 'app_order/order_pay_account.html'
    success_url = reverse_lazy('app_order:progress_payment')
    extra_context = {'type_of_delivery': SiteSettings.DELIVERY, 'type_of_payment': SiteSettings.PAY_TYPE}

    def get_template_names(self):
        super(PaymentView, self).get_template_names()
        templates_dict = {
            'online': 'app_order/pay_online.html',
            'someone': 'app_order/pay_someone.html'
        }
        order = self.get_object()
        name = templates_dict[order.pay]
        return name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs['pk']
        order = Order.objects.get(id=order_id)
        context['order'] = order
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


def validate_username(request):
    order_id = request.POST.get('order', None)
    number = int(str(request.POST.get('number', None)).replace(' ', ''))
    pay = request.POST.get('pay', None)
    task = pay_order.delay(order_id, number, pay)
    response = {
        "task_id": task.id,
        "task_status": task.status,
        "task_result": task.result,
        "success_url": redirect('app_order:success_pay', order_id).url,
        "failed_url": redirect('app_order:failed_pay', order_id).url,
        "order_id": order_id,
    }
    if task.result == 'error':
        error_dict = {'task_status': 'ERROR'}
        response.update(error_dict)
    return JsonResponse(response, status=202)


def get_status_payment(request, task_id, order_id):
    task_result = AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
        "success_url": redirect('app_order:success_pay', order_id).url,
        "failed_url": redirect('app_order:failed_pay', order_id).url,
        "order_id": order_id,
    }
    if task_result.result == 'error':
        error_dict = {'task_status': 'ERROR'}
        response.update(error_dict)
    return JsonResponse(response)

class ChangePayWay(TemplateView):
    pass
class PaymentProgress(TemplateView):
    template_name = 'app_order/progress_payment.html'


class ConfirmReceiptPurchase(UpdateView):
    """Класс-представления для подтверждения получения заказа."""
    model = Order
    template_name = 'app_order/order_detail.html'
    context_object_name = 'order'
    form_class = UpdateOrderStatusForm

    def post(self, request, *args, **kwargs):
        order_id = self.kwargs['order_id']
        order = Order.objects.get(id=order_id)
        form = UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.save()
            messages.success(self.request, f"Получение {order} подтверждено")
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)


class RejectOrder(UpdateView):
    """Класс-представления для отмены заказа."""
    model = Order
    template_name = 'app_order/order_list.html'
    context_object_name = 'order'
    form_class = UpdateOrderStatusForm

    def post(self, request, *args, **kwargs):
        order_id = self.kwargs['order_id']
        order = Order.objects.get(id=order_id)
        form = UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.save()
            messages.info(self.request, f"{order} отменен")
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)



class AddressList(ListView):
    model = Address
    template_name = 'app_user/customer/address_list.html'
    context_object_name = 'addresses'

    def get(self, request, *args, **kwargs):
        super(AddressList, self).get(request, *args, **kwargs)
        object_list = AddressHandler.get_address_list(self.request)
        form = AddressForm
        context = {'form': form, 'object_list': object_list}
        return render(request, self.template_name, context=context)


class AddressCreate(AddressList, CreateView):
    model = Address
    form_class = AddressForm

    def form_valid(self, form):
        address = form.save(commit=False)
        address.city = form.cleaned_data.get('city').title()
        address.user = self.request.user
        address.save()
        messages.add_message(self.request, messages.INFO, f"Новый адрес доставки сохранен")
        return redirect('app_order:address_list')

    def form_invalid(self, form):
        return redirect('app_order:address_list')


class AddressUpdate(AddressList, UpdateView):
    model = Address
    form_class = AddressForm

    def get_success_url(self):
        messages.add_message(self.request, messages.INFO, f"Данные адреса доставки изменены")
        return redirect('app_order:address_list')


class AddressDelete(DeleteView):
    model = Address

    def get(self, request, *args, **kwargs):
        address_id = kwargs['pk']
        AddressHandler.delete_address(request, address_id)
        messages.add_message(self.request, messages.INFO, f"Адрес  успешно удален")
        return redirect('app_order:address_list')
