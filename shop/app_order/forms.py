from django import forms

from app_cart.models import CartItem
from app_order.models import Order, Invoice, Address


class OrderCreateForm(forms.ModelForm):
    """Форма для создания заказа."""
    post_address = forms.CharField(max_length=200, label='сохраненный адрес', required=False)

    class Meta:
        model = Order
        fields = ('email', 'telephone', 'delivery', 'pay', 'city', 'address', 'name', 'post_address', 'comment' )


class CartItemUpdateForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ('quantity',)


class OrderUpdateForm(forms.ModelForm):
    """Форма для создания заказа."""

    class Meta:
        model = Order
        fields = ('email', 'telephone', 'delivery', 'pay', 'city', 'address', 'name', 'total_sum')


class PaymentForm(forms.ModelForm):
    """Форма для создания чека оплаты заказа."""

    class Meta:
        model = Invoice
        fields = ('order', 'number', 'recipient')


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('city', 'address')
