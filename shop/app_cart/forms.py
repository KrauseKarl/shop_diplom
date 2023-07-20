"""Модуль содержит формы для работы с корзиной."""
from django import forms
from django.core import validators


class AmountForm(forms.Form):
    """Форма для обновления кол-ва товара в корзине."""

    quantity = forms.IntegerField(
        label="quantity",
        min_value=0,
        validators=[validators.integer_validator],
    )
    update = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput
    )
