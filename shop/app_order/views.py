import time

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.management import call_command
from django.db import transaction
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView, RedirectView

from app_cart.context_processors import get_cart
from app_cart.models import Cart, CartItem
# from app_cart.services.cart_services import
from app_cart.services.cart_services import get_current_cart
from app_item.models import Item
from utils.my_utils import MixinPaginator
from app_store.models import Store

from app_order.forms import OrderForm, PaymentForm
from app_order.models import Order, Invoice
from app_order.services.order_services import get_order, Payment
from app_store.form import UpdateOrderStatusForm
from app_store.models import Store
from app_user.services.user_services import get_user


class OrderCreate(CreateView):
    model = Order
    form_class = OrderForm

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
        user = get_user(self.request.user)
        cart = get_current_cart(self.request).get('cart')
        stores = get_cart(self.request).get('cart_dict').get('book')

        # 3 create order (user, cart, form) # TODO service def _create_order(user, cart, form)
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')
        telephone = form.cleaned_data.get('telephone')
        delivery = form.cleaned_data.get('delivery')
        pay = form.cleaned_data.get('pay')
        city = form.cleaned_data.get('city')
        address = form.cleaned_data.get('address')
        # total_sum = int(form.cleaned_data.get('total_sum'))
        order_list = []
        with transaction.atomic():
            for store_title, values in stores.items():
                store = Store.objects.get(title=store_title)
                total_amount = values['total']
                order = Order.objects.create(
                    user=user,
                    name=name,
                    email=email,
                    telephone=telephone,
                    delivery=delivery,
                    pay=pay,
                    city=city,
                    address=address,
                    status='new',
                    total_sum=total_amount,
                    store=store,
                )
                order_list.append(order)
                items = cart.items.filter(
                    Q(is_paid=False) & Q(item__store=store))  # TODO service def _get_all_items_of_cart()

                for item in items:
                    item.is_paid = True  # TODO service def _set_item_is_paid()
                    item.order = order
                    item.save()

                    product = Item.objects.get(id=item.item.id)  # TODO service def _get_item()
                    product.stock -= item.quantity  # TODO service def _write_off_item_from_store()
                    product.save()
            # 5 TODO service def check_cart_paid()
            cart.is_archived = True
            cart.save()

            return render(self.request, 'app_order/successful_order.html', {'order': order_list, 'pay': pay})

    def form_invalid(self, form):
        return render(self.request, 'app_order/failed_order.html', {'v': form.errors})


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

    # permission_required = ('app_order.view_order', 'app_order.change_order')

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        if self.request.user.is_authenticated:
            queryset = cache.get(f'order_list_{request.user.get_full_name()}')
            if not queryset:
                queryset = get_order(user=self.request.user)
                cache.set(f'order_list_{request.user.get_full_name()}', queryset, 10000)

            if status:
                queryset = queryset.filter(status=status)
            object_list = self.my_paginator(queryset, self.request, self.paginate_by)

            context = {'object_list': object_list}
        else:
            context = {'object_list': None}

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
        context['items_is_paid'] = CartItem.objects.filter(order=self.get_object())  # TODO service def _get_has_paid_items
        return context


class SuccessPaid(TemplateView):
   pass
   # template_name = 'app_order/successful_pay.html'


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


class InvoicesList(ListView, MixinPaginator):
    """Класс-представления для получения списка всех квитанций об оплате."""
    model = Invoice
    template_name = 'app_user/customer/invoices_list.html'
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

class PaymentCardView(CreateView):
    pass
    # model = Invoice
    # template_name = 'app_order/order_pay_card.html'
    # form_class = PaymentForm
    # extra_context = {'new_orders': Order.objects.filter(is_paid=False)}
    #
    # def form_valid(self, form):
    #     orders_id = self.request.POST.getlist('order')
    #     orders = Order.objects.filter(id__in=orders_id)
    #     number = form.cleaned_data['number']
    #
    #     with transaction.atomic():
    #         for order in orders:
    #             store = Store.objects.get(orders=order)
    #             # order.status = 'in_progress'
    #             # order.is_paid = True
    #             # order.save()
    #             for product in order.items_is_paid.all():
    #                 item = Item.objects.get(cart_item=product.id)
    #                 item.stock -= product.quantity
    #                 item.save()
    #             invoice = Invoice.objects.create(
    #                 order=order,
    #                 number=number,
    #                 recipient=store,
    #             )
    #             # Payment.add_order_to_job(invoice.id)
    #             call_command('pay_command', invoice.id)
    #
    #     return redirect('app_order:progress_payment')
    #
    # def form_invalid(self, form):
    #     return super().form_invalid(form)


class PaymentAccountView(TemplateView):
    pass
    # model = Invoice
    # template_name = 'app_order/order_pay_account.html'
    # extra_context = {'new_orders': Order.objects.filter(is_paid=False)}


class PaymentOrderView(CreateView):
    pass
    # model = Invoice
    # form_class = PaymentForm
    #
    # def form_valid(self, form):
    #     orders_id = self.request.POST.getlist('order')
    #     orders = Order.objects.filter(id__in=orders_id)
    #     number = form.cleaned_data['number']
    #
    #     with transaction.atomic():
    #         for order in orders:
    #             store = Store.objects.get(orders=order)
    #             order.status = 'in_progress'
    #             order.is_paid = True
    #             order.save()
    #             for product in order.items_is_paid.all():
    #                 item = Item.objects.get(cart_item=product.id)
    #                 item.stock -= product.quantity
    #                 item.save()
    #             Invoice.objects.create(
    #                 order=order,
    #                 number=number,
    #                 recipient=store,
    #             )
    #
    #     return redirect('app_order:progress_payment')


class PaymentProgress(TemplateView):
    pass
    # template_name = 'app_order/progress_payment.html'
    # def get(self, request, *args, **kwargs):
    #     print('1#')
    #     time.sleep(5)
    #     print('2#')
    #     result = Payment.init_payment()
    #     print('3#', result)
    #     context = self.get_context_data(**kwargs)
    #     return self.render_to_response(context)
    #     # result = False
    #     # while result != True:
    #     #     result =
    #     # return self.render_to_response(context)
    #     # return redirect('app_order:success_pay')