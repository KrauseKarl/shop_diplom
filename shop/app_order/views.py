from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth import mixins
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic

# models
from app_order import models as order_models
from app_settings import models as settings_models
from app_invoice import models as invoice_models
# forms
from app_invoice import forms as invoice_forms
from app_order import forms as order_forms
from app_store import forms as store_forms
# services
from app_order.services import order_services
# others
from utils.my_utils import MixinPaginator, CustomerOnlyMixin
from app_order.tasks import paying


class OrderList(CustomerOnlyMixin, generic.ListView, MixinPaginator):
    """"""  # todo OrderList DOC
    model = order_models.Order
    template_name = 'app_order/order/order_list.html'
    context_object_name = 'orders'
    paginate_by = 3
    login_url = '/accounts/login/'
    redirect_field_name = 'login'

    def get_queryset(self, delivery_status=None):
        return order_services.CustomerOrderHandler.get_customer_order_list(self.request, delivery_status)

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


class OrderDetail(mixins.UserPassesTestMixin, generic.DetailView):
    """"""  # todo OrderDetail DOC
    model = order_models.Order
    template_name = 'app_order/order/order_detail.html'
    context_object_name = 'order'
    STATUS_LIST_ORDER = order_models.Order().STATUS
    STATUS_LIST_ITEM = order_models.OrderItem().STATUS

    def test_func(self):
        user = self.request.user
        order = self.get_object().user
        return True if user == order else False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = order_services.CustomerOrderHandler.get_order_items(order=self.get_object())
        context['status_list'] = self.STATUS_LIST_ORDER
        context['status_list_item'] = self.STATUS_LIST_ITEM
        context['invoice'] = invoice_models.Invoice.objects.filter(order=self.get_object()).filter()
        return context


class OrderCreate(generic.CreateView):
    """"""  # todo OrderCreate DOC
    model = order_models.Order
    form_class = order_forms.OrderCreateForm
    extra_context = {
        'type_of_delivery': settings_models.SiteSettings.DELIVERY,
        'type_of_payment': settings_models.SiteSettings.PAY_TYPE
    }
    MESSAGE = 'Заказ успешно сформирован'

    def get_template_names(self):
        super(OrderCreate, self).get_template_names()
        templates_dict = {
            True: 'app_order/order/create_order_auth.html',
            False: 'app_order/order/create_order_anon.html'
        }
        user_role = self.request.user.is_authenticated
        name = templates_dict[user_role]
        return name

    def form_valid(self, form):
        order = order_services.CustomerOrderHandler.create_order(self.request, form)
        messages.add_message(self.request, messages.INFO, self.MESSAGE)
        return redirect('app_order:progress_payment', order.id)

    def form_invalid(self, form):
        return render(self.request, 'app_order/failed_order.html', {'error': form.errors})


class OrderCancel(mixins.UserPassesTestMixin, generic.DeleteView):
    """
    Функция удаляет заказа.
    :return: возвращает на страницу списка заказов
    """
    model = order_models.Order
    template_name = 'app_order/order/order_cancel.html'
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


class OrderUpdatePayWay(mixins.UserPassesTestMixin, generic.UpdateView):
    """"""  # todo OrderUpdatePayWay DOC
    model = order_models.Order
    template_name = 'app_order/payment/order_update_pay_way.html'
    fields = ['pay']
    extra_context = {'type_of_payment': settings_models.SiteSettings().PAY_TYPE}

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def get_success_url(self):
        return reverse('app_order:progress_payment', kwargs={'pk': self.object.pk})


class SuccessOrdered(generic.TemplateView):
    """"""  # TODO SuccessOrdered
    template_name = 'app_order/order/success_order.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['order'] = order_models.Order.objects.filter(user=request.user).order_by('-id')
        return self.render_to_response(context)


class FailedOrdered(generic.TemplateView):
    """"""  # TODO FailedOrdered
    template_name = 'app_order/order/failed_order.html'


# PAYMENT
class PaymentView(CustomerOnlyMixin, generic.DetailView, generic.CreateView):
    """"""  # todo OrderCreate DOC
    model = order_models.Order
    form_class = invoice_forms.PaymentForm
    success_url = reverse_lazy('app_order:progress_payment')

    def get_template_names(self):
        super(PaymentView, self).get_template_names()
        templates_dict = {
            'online': 'app_order/payment/pay_online.html',
            'someone': 'app_order/payment/pay_someone.html'
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
        context['type_of_delivery'] = settings_models.SiteSettings.DELIVERY
        context['type_of_payment'] = settings_models.SiteSettings.PAY_TYPE
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class SuccessPaid(mixins.UserPassesTestMixin, generic.TemplateView):
    """"""  # todo SuccessPaid DOC
    template_name = 'app_order/payment/successful_pay.html'

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


class FailedPaid(mixins.UserPassesTestMixin, generic.TemplateView):
    """"""  # todo FailedPaid DOC
    template_name = 'app_order/payment/failed_pay.html'

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


def pay_order(request):
    """"""  # todo pay_order DOC
    order_id = request.POST.get('order', None)
    number = int(str(request.POST.get('number', None)).replace(' ', ''))
    pay = request.POST.get('pay', None)
    task = paying.delay(order_id, number, pay)
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
    """"""  # todo get_status_payment DOC
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

# MANIPULATE ORDER
class ConfirmReceiptPurchase(CustomerOnlyMixin, mixins.UserPassesTestMixin, generic.UpdateView):
    """Класс-представления для подтверждения получения заказа."""
    model = order_models.Order
    template_name = 'app_order/order/order_detail.html'
    context_object_name = 'order'
    form_class = store_forms.UpdateOrderStatusForm

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        form = store_forms.UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.order_items.update(status=status)
            order.save(update_fields=['status'])
            messages.success(self.request, f"Получение {order} подтверждено")
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)


class RejectOrder(CustomerOnlyMixin, mixins.UserPassesTestMixin, generic.UpdateView):
    """Класс-представления для отмены заказа."""
    model = order_models.Order
    template_name = 'app_order/order/order_list.html'
    context_object_name = 'order'
    form_class = store_forms.UpdateOrderStatusForm

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.user else False

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        form = store_forms.UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.order_items.update(status='deactivated')
            order.save()
            messages.add_message(self.request, messages.INFO, f"{order} отменен")
            path = self.request.META.get('HTTP_REFERER')
            return redirect(path)

