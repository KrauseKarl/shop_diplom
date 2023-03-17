from django import forms
from app_invoice.models import Invoice


class PaymentForm(forms.ModelForm):
    """Форма для создания чека оплаты заказа."""
    pay = forms.CharField(max_length=200, empty_value='online', required=False)

    class Meta:
        model = Invoice
        fields = ('order', 'number', 'pay')
