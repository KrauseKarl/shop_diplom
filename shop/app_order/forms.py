from django import forms
from app_order import models as order_models


class OrderCreateForm(forms.ModelForm):
    """Форма для создания заказа."""

    post_address = forms.CharField(
        max_length=200, label="сохраненный адрес", required=False
    )

    class Meta:
        model = order_models.Order
        fields = (
            "email",
            "telephone",
            "delivery",
            "pay",
            "city",
            "address",
            "name",
            "post_address",
            "comment",
            "total_sum",
        )


class OrderItemUpdateForm(forms.ModelForm):
    """Форма для редактировнаие товара в заказе."""

    class Meta:
        model = order_models.OrderItem
        fields = ("quantity",)


class OrderUpdateForm(forms.ModelForm):
    """Форма для редактировнаие заказа."""

    class Meta:
        model = order_models.Order
        fields = (
            "email",
            "telephone",
            "delivery",
            "pay",
            "city",
            "address",
            "name",
            "total_sum",
        )
