"""Модуль содержит формы для работы с товарми и комментариями."""
from django import forms
from django.utils.safestring import mark_safe

from app_item.models import Comment, Item


class CommentForm(forms.ModelForm):
    """Форма для создания комментария."""

    class Meta:
        model = Comment
        fields = ("review",)


class ItemForm(forms.ModelForm):
    """Форма для создания товара."""

    colors = [
        "red",
        "orange",
        "yellow",
        "green",
        "blue",
        "magenta",
        "white",
        "black",
        "grey",
    ]

    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        """Функция для замены текстового значения цвет на цвет из палитры."""
        widget = self.fields["color"].widget
        choices = []
        for key, value in widget.choices:
            if key in self.colors:
                value = mark_safe(
                    f'<div type="radio" style="background-color:{value};'
                    f"height:20px; width:30px; position: relative; float: left;"
                    f"border-radius: 20px; box-shadow: 0 0 5px; "
                    f'margin: 0 5px; padding:2px"></div>'
                )
                choices.append((key, value))
        widget.choices = choices

    class Meta:
        model = Item
        fields = "__all__"
