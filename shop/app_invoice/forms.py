from django import forms
from app_invoice import models as invoice_models
from app_order import models as order_models


class PaymentForm(forms.ModelForm):
    """Форма для создания чека оплаты заказа."""
    pay = forms.CharField(max_length=200, empty_value='online', required=False)

    class Meta:
        model = invoice_models.Invoice
        fields = ('order', 'number', 'pay')


class AddressForm(forms.ModelForm):
    """Форма для создания адреса доставки заказа."""
    class Meta:
        model = order_models.Address
        fields = ('city', 'address')
