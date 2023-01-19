from django import forms

from app_order.models import Order, Invoice
from app_store.models import Store


class OrderForm(forms.ModelForm):
    # TODO OrderForm description
    class Meta:
        model = Order
        fields = ('email', 'telephone', 'delivery', 'pay', 'city', 'address', 'name', 'total_sum')


class PaymentForm(forms.ModelForm):
    # TODO PaymentForm description
    class Meta:
        model = Invoice
        fields = ('order', 'number')
