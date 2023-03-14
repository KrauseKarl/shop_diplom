from django import forms
from django.forms import modelformset_factory

from app_item.models import Item, Tag, Image, Category, FeatureValue, Feature
from app_order.models import Order
from app_store.models import Store


class CreateStoreForm(forms.ModelForm):
    """Форма для создания магазина."""

    class Meta:
        model = Store
        fields = ('title', 'logo', 'discount', 'min_for_discount')


class UpdateStoreForm(forms.ModelForm):
    """Форма для редактирования магазина."""

    class Meta:
        model = Store
        fields = ('title', 'logo', 'discount', 'min_for_discount', 'is_active')


class AddItemForm(forms.ModelForm):
    """Форма для создания товара."""

    class Meta:
        model = Item
        fields = (
            'title',
            'description',
            'stock',
            'price',
            'is_available',
            'limited_edition',
            'color',
            'tag',
            'category'
        )


class AddItemImageForm(forms.ModelForm):
    """Форма для создания изображения товара."""
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        label='Изображения',
        required=False)

    class Meta(AddItemForm.Meta):
        fields = AddItemForm.Meta.fields + ('image',)


class UpdateItemForm(forms.ModelForm):
    """Форма для редактирования товара."""

    class Meta:
        model = Item
        fields = (
            'title',
            'description',
            'stock',
            'price',
            'is_available',
            'limited_edition',
            'color',
            'category',
        )


class UpdateItemImageForm(forms.ModelForm):
    """Форма для редактирования изображения товара."""
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        label='Изображения',
        required=False)

    class Meta(UpdateItemForm.Meta):
        fields = UpdateItemForm.Meta.fields + ('image',)


TagFormSet = modelformset_factory(
    Tag,
    fields=("title",),
    extra=1
)
ImageFormSet = modelformset_factory(
    Image,
    fields=("image",),
    extra=1
)
FeatureFormSet = modelformset_factory(
    FeatureValue,
    fields=("value",),
    extra=1
)


class CreateTagForm(forms.ModelForm):
    """Форма для создания тега."""

    class Meta:
        model = Tag
        fields = ('title',)


class AddTagForm(forms.ModelForm):
    """Форма для добавления тега в карточку товара."""

    class Meta:
        model = Item
        fields = ('tag',)


class CreateCategoryForm(forms.ModelForm):
    """Форма для создания категории товаров."""
    my_default_errors = {
        'required': 'Это поле является обязательным',
        'invalid': 'Категория с таким названием уже существует'
    }
    title = forms.CharField(error_messages=my_default_errors)

    class Meta:
        model = Category
        fields = ('parent_category', 'title', 'description',)


class CreateFeatureForm(forms.ModelForm):
    """Форма для создания характеристики."""
    category = forms.CharField(max_length=200)

    class Meta:
        model = Feature
        fields = ('title', 'category')


class CreateValueForm(forms.ModelForm):
    """Форма для создания характеристики."""

    class Meta:
        model = FeatureValue
        fields = ('value', 'feature',)


class ImportDataFromCVS(forms.Form):
    """Форма для импорта данных."""
    file = forms.FileField()


class UpdateOrderStatusForm(forms.ModelForm):
    """Форма для экспорта данных."""

    class Meta:
        model = Order
        fields = ('status',)
