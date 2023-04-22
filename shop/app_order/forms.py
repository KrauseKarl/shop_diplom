from django import forms

from app_cart.models import CartItem
from app_order.models import Order, Address, OrderItem


class OrderCreateForm(forms.ModelForm):
    """Форма для создания заказа."""
    post_address = forms.CharField(max_length=200, label='сохраненный адрес', required=False)

    class Meta:
        model = Order
        fields = ('email', 'telephone', 'delivery', 'pay', 'city', 'address', 'name', 'post_address', 'comment', 'total_sum')


class OrderItemUpdateForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ('quantity',)


class OrderUpdateForm(forms.ModelForm):
    """Форма для создания заказа."""

    class Meta:
        model = Order
        fields = ('email', 'telephone', 'delivery', 'pay', 'city', 'address', 'name', 'total_sum')




class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('city', 'address')
