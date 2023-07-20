from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

# models
from app_item import models as item_models
from app_order import models as order_models
from app_store import models as store_models


class CreateStoreForm(forms.ModelForm):
    """Форма для создания магазина."""

    class Meta:
        model = store_models.Store
        fields = (
            "title",
            "logo",
            "discount",
            "min_for_discount",
            "is_active",
            "description",
            "is_active",
            "owner",
        )


class UpdateStoreForm(forms.ModelForm):
    """Форма для редактирования магазина."""

    class Meta:
        model = store_models.Store
        fields = (
            "title",
            "logo",
            "discount",
            "min_for_discount",
            "is_active",
            "description",
            "is_active",
            "owner",
        )


class CustomMMCF(forms.ModelMultipleChoiceField):
    def label_from_instance(self, tag):
        return f"{tag.title}"


class AddItemForm(forms.ModelForm):
    """Форма для создания товара."""

    tag = CustomMMCF(
        queryset=item_models.Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = item_models.Item
        fields = (
            "title",
            "description",
            "stock",
            "price",
            "is_available",
            "limited_edition",
            "color",
            "tag",
            "category",
        )


def file_size(value):
    """Функция валидирует размер загружаемого файла."""
    limit = 2 * 1024 * 1024
    if value.size > limit:
        raise ValidationError("Файл слишком большой. Размер не должен превышать 2 МБ.")


class AddItemImageForm(forms.ModelForm):
    """Форма для создания изображения товара."""

    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        label="Изображения",
        required=False,
        validators=[file_size],
    )

    class Meta(AddItemForm.Meta):
        fields = AddItemForm.Meta.fields + ("image",)


class UpdateItemForm(forms.ModelForm):
    """Форма для редактирования товара."""

    class Meta:
        model = item_models.Item
        fields = (
            "title",
            "description",
            "stock",
            "price",
            "is_available",
            "limited_edition",
            "color",
            "category",
        )


class UpdateItemImageForm(forms.ModelForm):
    """Форма для редактирования изображения товара."""

    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        label="Изображения",
        required=False,
        validators=[file_size],
    )

    class Meta(UpdateItemForm.Meta):
        fields = UpdateItemForm.Meta.fields + ("image",)

    def clean_image_size(self):
        """Функция валидирует размер загружаемого файла."""

        limit = 2 * 1024 * 1024
        img = self.cleaned_data.get("image")
        if img.size > limit:
            raise ValidationError("Размер файла не должен превышать 2 МБ")
        return img


TagFormSet = modelformset_factory(
    item_models.Tag, fields=("title",), extra=1, error_messages="Укажите тег"
)
ImageFormSet = modelformset_factory(item_models.Image, fields=("image",), extra=1)
FeatureFormSet = modelformset_factory(
    item_models.FeatureValue, fields=("value",), extra=1
)


class CreateTagForm(forms.ModelForm):
    """Форма для создания тега."""

    class Meta:
        model = item_models.Tag
        fields = ("title",)

    def clean_tag(self):
        """Функция валидирует сущетвование тег в базе данных."""

        tag = self.cleaned_data.get("category").lower()
        if item_models.Tag.objects.get(title=tag).exist():
            raise ValidationError("Такая категория уже существует")
        return tag


class AddTagForm(forms.ModelForm):
    """Форма для добавления тега в карточку товара."""

    tag = CustomMMCF(
        queryset=item_models.Tag.objects.all(), widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = item_models.Item
        fields = ("tag",)


class CreateFeatureForm(forms.ModelForm):
    """Форма для создания характеристики."""

    class Meta:
        model = item_models.Feature
        fields = ("title",)

    def clean_feature(self):
        """Функция валидирует сущетвование характеристики в базе данных."""

        feature = self.cleaned_data.get("title").lower()
        if item_models.Feature.objects.get(title=feature).exist():
            raise ValidationError("Такая характеристика уже существует")
        return feature


class CreateValueForm(forms.ModelForm):
    """Форма для создания характеристики."""

    class Meta:
        model = item_models.FeatureValue
        fields = ("value",)

    def clean_value(self):
        """Функция валидирует сущетвование значене характеристики в базе данных"""

        value = self.cleaned_data.get("value").lower()
        if item_models.FeatureValue.objects.filter(value=value).first():
            raise ValidationError("Такое значение  уже существует")
        else:
            return value


class ImportDataFromCVS(forms.Form):
    """Форма для импорта данных."""

    file = forms.FileField()


class UpdateOrderStatusForm(forms.ModelForm):
    """Форма для отправки заказа."""

    class Meta:
        model = order_models.Order
        fields = ("status",)


class OrderSearchForm(forms.ModelForm):
    start = forms.DateTimeField(required=False)
    finish = forms.DateTimeField(required=False)
    store = forms.CharField(required=False)
    status = forms.CharField(required=False)
    search = forms.CharField(required=False)

    class Meta:
        model = order_models.Order
        fields = (
            "status",
            "search",
            "store",
            "start",
            "finish",
        )
