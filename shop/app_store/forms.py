from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from PIL import Image as PilImage
from app_item.models import Item, Tag, Image, Category, FeatureValue, Feature
from app_item.services.item_services import ImageHandler
from app_order.models import Order
from app_store.models import Store


class CreateStoreForm(forms.ModelForm):
    """Форма для создания магазина."""

    class Meta:
        model = Store
        fields = ('title', 'logo', 'discount', 'min_for_discount', 'is_active', 'description', 'is_active', 'owner')


class UpdateStoreForm(forms.ModelForm):
    """Форма для редактирования магазина."""

    class Meta:
        model = Store
        fields = ('title', 'logo', 'discount', 'min_for_discount', 'is_active', 'description', 'is_active', 'owner')


class CustomMMCF(forms.ModelMultipleChoiceField):
    def label_from_instance(self, tag):
        return f"{tag.title}"


class AddItemForm(forms.ModelForm):
    """Форма для создания товара."""
    tag = CustomMMCF(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

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


def file_size(value):
    """Функция валидирует размер загружаемого файла."""
    limit = 2 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('Файл слишком большой. Размер не должен превышать 2 МБ.')


class AddItemImageForm(forms.ModelForm):
    """Форма для создания изображения товара."""
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        label='Изображения',
        required=False,
        validators=[file_size],
        )

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
        required=False,
        validators=[file_size],
    )

    class Meta:
        model = Image
        fields = ('image', )

    def clean_image_size(self):
        """Функция валидирует размер загружаемого файла."""
        limit = 2 * 1024 * 1024
        img = self.cleaned_data.get('image')
        if img.size > limit:
            raise ValidationError('Размер файла не должен превышать 2 МБ')
        return img


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

    def clean_tag(self):
        """Функция валидирует сущетвование тег в базе данных"""
        tag = self.cleaned_data.get('category').lower()
        if Tag.objects.get(title=tag).exist():
            raise ValidationError('Такая категория уже существует')
        return tag


class AddTagForm(forms.ModelForm):
    """Форма для добавления тега в карточку товара."""
    tag = CustomMMCF(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Item
        fields = ('tag',)


# class CreateCategoryForm(forms.ModelForm):
#     """Форма для создания категории товаров."""
#     my_default_errors = {
#         'required': 'Это поле является обязательным',
#         'invalid': 'Категория с таким названием уже существует'
#     }
#     title = forms.CharField(error_messages=my_default_errors)
#
#     class Meta:
#         model = Category
#         fields = ('parent_category', 'title', 'description',)
#
#     def clean_category(self):
#         """Функция валидирует сущетвование категории в базе данных"""
#         category = self.cleaned_data.get('category').lower()
#         if Category.objects.get(title=category).exist():
#             raise ValidationError('Такая категория уже существует')
#         return category


class CreateFeatureForm(forms.ModelForm):
    """Форма для создания характеристики."""

    class Meta:
        model = Feature
        fields = ('title', )

    def clean_feature(self):
        """Функция валидирует сущетвование характеристики в базе данных"""
        feature = self.cleaned_data.get('title').lower()
        if Feature.objects.get(title=feature).exist():
            raise ValidationError('Такая характеристика уже существует')
        return feature


class CreateValueForm(forms.ModelForm):
    """Форма для создания характеристики."""

    class Meta:
        model = FeatureValue
        fields = ('value',)

    def clean_value(self):
        """Функция валидирует сущетвование значене характеристики в базе данных"""

        value = self.cleaned_data.get('value').lower()
        if FeatureValue.objects.filter(value=value).first():
            raise ValidationError('Такое значение  уже существует')
        else:
            return value


class ImportDataFromCVS(forms.Form):
    """Форма для импорта данных."""
    file = forms.FileField()


class UpdateOrderStatusForm(forms.ModelForm):
    """Форма для отправки заказа."""

    class Meta:
        model = Order
        fields = ('status',)


class OrderSearchForm(forms.ModelForm):
    start = forms.DateTimeField(required=False)
    finish = forms.DateTimeField(required=False)
    store = forms.CharField(required=False)
    status = forms.CharField(required=False)
    search = forms.CharField(required=False)

    class Meta:
        model = Order
        fields = ('status', 'search', 'store', 'start', 'finish',)
