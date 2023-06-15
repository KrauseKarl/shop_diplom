from django import forms
from django.core.exceptions import ValidationError

from app_item import models as item_modals
from app_settings import models as settings_models


class UpdateSettingsForm(forms.ModelForm):
    class Meta:
        model = settings_models.SiteSettings
        fields = (
            'express_delivery_price',
            'min_free_delivery',
            'delivery_fees',
            'cache_detail_view',
            'url',
            'title',
            'support_email',
            'phone',
            'skype',
            'address',
            'facebook',
            'twitter',
            'linkedIn',
        )


# CATEGORY FORMS
class CreateCategoryForm(forms.ModelForm):
    """Форма для создания категории товаров."""
    my_default_errors = {
        'required': 'Это поле является обязательным',
        'invalid': 'Категория с таким названием уже существует'
    }
    title = forms.CharField(error_messages=my_default_errors)

    class Meta:
        model = item_modals.Category
        fields = ('parent_category', 'title', 'description',)

    def clean_category(self):
        """Функция валидирует сущетвование категории в базе данных"""
        category = self.cleaned_data.get('category').lower()
        if item_modals.Category.objects.get(title=category).exist():
            raise ValidationError('Такая категория уже существует')
        return category


class UpdateCategoryForm(forms.ModelForm):
    """Форма для создания категории товаров."""
    my_default_errors = {
        'required': 'Это поле является обязательным',
        'invalid': 'Категория с таким названием уже существует'
    }

    class Meta:
        model = item_modals.Category
        fields = ('parent_category', 'title', 'description',)


# TAG FORMS
class CreateTagForm(forms.ModelForm):
    """Форма для создания тега."""
    class Meta:
        model = item_modals.Tag
        fields = ('title',)

    def clean_tag(self):
        """Функция валидирует сущетвование тег в базе данных"""
        tag = self.cleaned_data.get('category').lower()
        if item_modals.Tag.objects.get(title=tag).exist():
            raise ValidationError('Такая категория уже существует')
        return tag



# FEATURE & VALUE FORMS
class CreateFeatureForm(forms.ModelForm):
    """Форма для создания характеристики."""

    class Meta:
        model = item_modals.Feature
        fields = ('title', )

    def clean_feature(self):
        """Функция валидирует сущетвование характеристики в базе данных"""
        feature = self.cleaned_data.get('title').lower()
        if item_modals.Feature.objects.get(title=feature).exist():
            raise ValidationError('Такая характеристика уже существует')
        return feature


class UpdateFeatureForm(forms.ModelForm):
    """Форма для обновления характеристики."""
    class Meta:
        model = item_modals.Feature
        fields = ('title', )