from django import forms
from django.forms import modelformset_factory, ModelChoiceField, Select

from app_item.models import Item, Tag, Image, Category
from app_order.models import Order
from app_store.models import Store


class CreateStoreForm(forms.ModelForm):
    # TODO CreateStoreForm description
    class Meta:
        model = Store
        fields = ('title', 'logo', 'delivery_fees', 'min_free_delivery')


class UpdateStoreForm(forms.ModelForm):
    # TODO UpdateStoreForm description
    class Meta:
        model = Store
        fields = ('title', 'logo', 'delivery_fees', 'min_free_delivery', 'is_active')


class AddForm(forms.ModelForm):
    # TODO AddForm description
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


class AddItemForm(forms.ModelForm):
    # TODO AddItemForm description
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        label='Изображения',
        required=False)

    class Meta(AddForm.Meta):
        fields = AddForm.Meta.fields + ('image',)


class UpdateForm(forms.ModelForm):
    # TODO UpdateForm description
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
            'category'
        )


class UpdateItemForm(forms.ModelForm):
    # TODO UpdateItemForm description
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        label='Изображения',
        required=False)

    class Meta(UpdateForm.Meta):
        fields = UpdateForm.Meta.fields + ('image',)


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


class AddTagForm(forms.ModelForm):
    # TODO AddTagForm description
    class Meta:
        model = Item
        fields = ('tag',)


class CreateTagForm(forms.ModelForm):
    # TODO CreateTagForm description
    class Meta:
        model = Tag
        fields = ('title',)


class CreateCategoryForm(forms.ModelForm):
    # TODO CreateCategoryForm description
    my_default_errors = {
        'required': 'Это поле является обязательным',
        'invalid': 'Категория с таким названием уже существует'
    }
    title = forms.CharField(error_messages=my_default_errors)

    class Meta:
        model = Category
        fields = ('parent_category', 'title', 'description',)


class ImportDataFromCVS(forms.Form):
    # TODO ImportDataFromCVS description
    file = forms.FileField()


class UpdateOrderStatusForm(forms.ModelForm):
    # TODO UpdateOrderStatusForm description
    class Meta:
        model = Order
        fields = ('status',)
