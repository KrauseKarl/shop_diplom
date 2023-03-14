from django import forms
from app_invoice.models import Invoice


class PaymentForm(forms.ModelForm):
    """Форма для создания чека оплаты заказа."""

    class Meta:
        model = Invoice
        fields = ('order', 'number')
