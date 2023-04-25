from time import sleep

from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
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
from utils.my_utils import MixinPaginator, CustomerOnlyMixin
from app_order.forms import OrderCreateForm, AddressForm
from app_order import models as order_models
from app_order.services.order_services import CustomerOrderHandler, AddressHandler, Payment
from app_order.tasks import pay_order
from app_store.forms import UpdateOrderStatusForm
from app_store.models import Store


class OrderCreate(CreateView):
    model = order_models.Order
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
        order = CustomerOrderHandler.create_order(self.request, form)
        return redirect('app_order:progress_payment', order.id)

    def form_invalid(self, form):
        return render(self.request, 'app_order/failed_order.html', {'error': form.errors})


class SuccessOrdered(TemplateView):
    template_name = 'app_order/successful_order.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['order'] = order_models.Order.objects.filter(user=request.user).order_by('-id')
        return self.render_to_response(context)


class FailedOrdered(TemplateView):
    template_name = 'app_order/failed_order.html'


class OrderList(CustomerOnlyMixin, ListView, MixinPaginator):
    model = order_models.Order
    template_name = 'app_order/order_list.html'
    context_object_name = 'orders'
    paginate_by = 3
    login_url = '/accounts/login/'
    redirect_field_name = 'login'

    # permission_required = ('app_order.view_order', 'app_order.change_order')

    def get_queryset(self, delivery_status=None):
        return CustomerOrderHandler.get_customer_order_list(self.request, delivery_status)

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        if self.request.user.is_authenticated:
            delivery_status = self.request.GET.get('status')
            queryset = self.get_queryset(delivery_status)
            object_list = MixinPaginator(queryset, request, self.paginate_by).my_paginator()
            context = {'object_list': object_list, 'status_list': order_models.Order.STATUS}
        else:
            context = {'object_list': None, 'status_list': order_models.OrderItem().STATUS}
        return render(request, self.template_name, context=context)


class OrderDetail(UserPassesTestMixin, DetailView):
    model = order_models.Order
    template_name = 'app_order/order_detail.html'
    context_object_name = 'order'

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = CustomerOrderHandler.get_order_items(order=self.get_object())
        print(context['order_items'])
        return context


class OrderCancel(UserPassesTestMixin, DeleteView):
    """
    Функция удаляет заказа.
    :return: возвращает на страницу списка заказов
    """
    model = order_models.Order
    template_name = 'app_order/order_cancel.html'
    success_url = reverse_lazy('app_order:order_list')
    message = 'Заказ отменен'

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def form_valid(self, form):
        self.object.delete()
        messages.add_message(self.request, messages.INFO, self.message)
        return HttpResponseRedirect(self.get_success_url())


class OrderUpdatePayWay(UserPassesTestMixin, UpdateView):
    model = order_models.Order
    template_name = 'app_order/order_update_pay_way.html'
    fields = ['pay']
    extra_context = {'type_of_payment': SiteSettings().PAY_TYPE}

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def get_success_url(self):
        return reverse('app_order:progress_payment', kwargs={'pk': self.object.pk})


class SuccessPaid(UserPassesTestMixin, TemplateView):
    template_name = 'app_order/successful_pay.html'

    def test_func(self):
        order_id = self.kwargs['order_id']
        order = order_models.Order.objects.get(id=order_id)
        if order.user == self.request.user:
            return True
        return False

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        order = order_models.Order.objects.get(id=kwargs['order_id'])
        context['order'] = order
        context['invoice'] = order.invoices.first
        return self.render_to_response(context)


class FailedPaid(UserPassesTestMixin, TemplateView):
    template_name = 'app_order/failed_pay.html'

    def test_func(self):
        order_id = self.kwargs['order_id']
        order = order_models.Order.objects.get(id=order_id)
        if order.user == self.request.user:
            return True
        return False

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        context['order'] = kwargs['order_id']
        order = order_models.Order.objects.get(id=kwargs['order_id'])
        context['error'] = order.error
        return self.render_to_response(context)


class PaymentView(CustomerOnlyMixin, DetailView, CreateView):
    model = order_models.Order
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
        order = self.get_object()
        if order.is_paid:
            raise Http404('Заказ уже оплачен')
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


class PaymentProgress(TemplateView):
    template_name = 'app_order/progress_payment.html'


class ConfirmReceiptPurchase(CustomerOnlyMixin, UserPassesTestMixin, UpdateView):
    """Класс-представления для подтверждения получения заказа."""
    model = order_models.Order
    template_name = 'app_order/order_detail.html'
    context_object_name = 'order'
    form_class = UpdateOrderStatusForm

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        form = UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.save()
            messages.success(self.request, f"Получение {order} подтверждено")
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)


class RejectOrder(CustomerOnlyMixin, UserPassesTestMixin, UpdateView):
    """Класс-представления для отмены заказа."""
    model = order_models.Order
    template_name = 'app_order/order_list.html'
    context_object_name = 'order'
    form_class = UpdateOrderStatusForm

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        form = UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.order_items.update(status='deactivated')
            order.save()
            messages.info(self.request, f"{order} отменен")
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)


class AddressList(LoginRequiredMixin, ListView):
    model = order_models.Address
    template_name = 'app_user/customer/address_list.html'
    context_object_name = 'addresses'

    # def test_func(self):
    #     user = self.request.user
    #     address = self.get_object()
    #     return True if user == address.user else False

    def get(self, request, *args, **kwargs):
        super(AddressList, self).get(request, *args, **kwargs)
        object_list = AddressHandler.get_address_list(self.request)
        form = AddressForm
        context = {'form': form, 'object_list': object_list}
        return render(request, self.template_name, context=context)


class AddressCreate(AddressList, CreateView):
    model = order_models.Address
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


class AddressUpdate(CustomerOnlyMixin, AddressList, UpdateView):
    model = order_models.Address
    form_class = AddressForm

    def test_func(self):
        user = self.request.user
        address = self.get_object()
        return True if user == address.user else False

    def get_success_url(self):
        messages.add_message(self.request, messages.INFO, f"Данные адреса доставки изменены")
        return redirect('app_order:address_list')


class AddressDelete(CustomerOnlyMixin, UserPassesTestMixin, DeleteView):
    model = order_models.Address

    def test_func(self):
        user = self.request.user
        address = self.get_object()
        return True if user == address.user else False

    def get(self, request, *args, **kwargs):
        address_id = kwargs['pk']
        AddressHandler.delete_address(request, address_id)
        messages.add_message(self.request, messages.INFO, f"Адрес  успешно удален")
        return redirect('app_order:address_list')
