import datetime
import os
import random
from io import BytesIO, StringIO
from PIL import Image as PilImage
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import Q, Count
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MinLengthValidator

from utils.my_utils import slugify_for_cyrillic_text
from app_store.models import Store
from app_item.managers import app_item_managers


class IpAddress(models.Model):
    ip = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ip_address',
        verbose_name='пользователь',
        blank=True,
        null=True,
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    objects = models.Manager()

    class Meta:
        db_table = 'app_ip_address'
        verbose_name = 'ip-адрес'
        verbose_name_plural = 'ip-адреса'

    def __str__(self):
        return self.ip


class Item(models.Model):
    """Модель товара."""
    RED = 'red'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    MAGENTA = 'magenta'
    WHITE = 'white'
    BLACK = 'black'
    BROWN = 'brown'

    COLOURS = (
        (RED, 'red'),
        (ORANGE, 'orange'),
        (YELLOW, 'yellow'),
        (GREEN, 'green'),
        (BLUE, 'blue'),
        (MAGENTA, 'magenta'),
        (WHITE, 'white'),
        (BLACK, 'black'),
        (BROWN, 'brown'),
    )
    DEFAULT_IMAGE = '/media/default_images/default_item.png'
    title = models.CharField(
        max_length=100,
        validators=[MinLengthValidator, ],
        db_index=True,
        verbose_name='название'
    )
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        allow_unicode=False,
        verbose_name='slug'
    )
    description = models.TextField(
        default='',
        blank=True,
        verbose_name='описание'
    )
    stock = models.PositiveIntegerField(
        verbose_name='количество'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator, ],
        verbose_name='цена'
    )
    is_available = models.BooleanField(
        default=False,
        verbose_name='в наличии'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='архивный товар'
    )
    limited_edition = models.BooleanField(
        default=False,
        verbose_name='ограниченный тираж'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата обновления'
    )
    color = models.CharField(
        max_length=10,
        choices=COLOURS,
        null=True,
        blank=True,
        verbose_name='цвет товара'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        null=True,
        related_name='items',
        verbose_name='категория'
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='items',
        verbose_name='магазин'
    )
    views = models.ManyToManyField(
        'IpAddress',
        related_name="item_views",
        blank=True,
        verbose_name='просмотры'
    )
    images = models.ManyToManyField(
        'Image',
        blank=True,
        related_name='item_images',
        verbose_name='изображение',

    )
    tag = models.ManyToManyField(
        'Tag',
        max_length=20,
        blank=True,
        related_name='item_tags',
        verbose_name='тег'
    )

    feature_value = models.ManyToManyField(
        'FeatureValue',
        max_length=20,
        blank=True,
        related_name='item_features',
        verbose_name='характеристика'
    )

    objects = models.Manager()
    available_items = app_item_managers.AvailableItemManager()
    unavailable_items = app_item_managers.UnavailableItemManager()
    limited_items = app_item_managers.LimitedEditionManager()

    class Meta:
        db_table = 'app_items'
        ordering = ['created']
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('app_item:item_detail', kwargs={'pk': self.pk})

    def get_category_url(self):
        return self.category.get_absolute_url()

    def get_store_url(self):
        try:
            return self.store.get_absolute_url()
        except ObjectDoesNotExist:
            return reverse('main_page')

    def save(self, *args, **kwargs):
        """Функция по созданию slug"""
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.title)
        self.updated = datetime.datetime.now()
        return super().save(*args, **kwargs)

    @property
    def main_image(self):
        """Функция возвращает URL главного изображения товара."""
        try:
            return self.images.first().image.url
        except (ObjectDoesNotExist, AttributeError):
            return self.DEFAULT_IMAGE

    @property
    def other_images(self):
        """Функция возвращает все изображения товара кроме первого."""
        try:
            return self.images.all()[1:]
        except (ObjectDoesNotExist, AttributeError):
            return None

    def total_views(self):
        """Функция возвращает общее количество просмотров для товара."""
        return self.views.count()

    @property
    def item_price(self):
        return self.price

    @property
    def get_store(self):
        return self.store

    @property
    def comments(self):
        return self.item_comments.filter(is_published=True)

    @property
    def purchases(self):
        return self.cart_item.aggregate(bestseller=Count('order_item__quantity')).get('bestseller')


class Category(models.Model):
    """Модель категории товара."""
    title = models.CharField(
        max_length=100,
        verbose_name='название',
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        allow_unicode=False
    )
    description = models.TextField(
        blank=True,
        verbose_name='описание'
    )
    image = models.ImageField(
        upload_to='category',
        null=True,
        verbose_name='иконка'
    )
    parent_category = models.ForeignKey(
        'self',
        related_name='sub_categories',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='родительская категория'
    )
    feature = models.ManyToManyField(
        'Feature',
        max_length=200,
        blank=True,
        related_name='categories',
        verbose_name='характеристика'
    )

    objects = app_item_managers.CategoryWithItemsManager()

    class Meta:
        db_table = 'app_categories'
        ordering = ('title',)
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Функция по созданию slug."""
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.title)
        super(Category, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('app_item:item_category', kwargs={'category': self.slug})

    def get_parent_url(self):
        return reverse('app_item:item_category', kwargs={'category': self.parent_category.slug})

    def item_count(self):
        """Функция по количеству товаров в конкретной категории."""
        return Item.available_items.filter(Q(category__parent_category=self) | Q(category=self)).count()


class Tag(models.Model):
    """Модель тега."""
    title = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name='название тега'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='активный'
    )

    objects = models.Manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('app_item:item_tag', kwargs={'tag': self.slug})

    class Meta:
        db_table = 'app_tags'
        ordering = ('title',)
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def save(self, *args, **kwargs):
        """Функция по созданию slug"""
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.title)
        super(Tag, self).save(*args, **kwargs)


class Comment(models.Model):
    """Модель комментария."""
    review = models.TextField(
        verbose_name='комментарий'
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='опубликовано'
    )
    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='item_comments',
        verbose_name='товар'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_comments',
        verbose_name='пользователь'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата обновления'
    )
    archived = models.BooleanField(default=False,
                                   verbose_name='удален в архив')
    objects = models.Manager()
    published_comments = app_item_managers.ModeratedCommentsManager()

    class Meta:
        db_table = 'app_comments'
        ordering = ['-created']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'комментарий №{self.pk}'

    def get_absolute_url(self):
        return reverse('app_store:comment_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        """Функция по созданию slug"""
        self.updated = datetime.datetime.now()
        super(Comment, self).save(*args, **kwargs)


class Image(models.Model):
    """Модель изображения."""
    FORMAT = 'PNG'
    QUALITY = 75
    WIDTH = 600

    title = models.CharField(
        max_length=200,
        null=True,
        verbose_name='название'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата изменения'
    )
    image = models.ImageField(
        upload_to='gallery/%Y/%m/%d',
        default='assets/img/default/default_item.png',
        null=True,
        blank=True,
        verbose_name='изображение'
    )

    objects = models.Manager()

    class Meta:
        db_table = 'app_images'
        ordering = ['title']
        verbose_name = 'изображение'
        verbose_name_plural = 'изображения'

    def __str__(self):
        return f'img - {self.pk}'

    def save(self, *args, **kwargs):
        from app_item.services.item_services import ImageHandler
        if self.pk is None:
            self.image = ImageHandler.resize_uploaded_image(
                image=self.image,
                title=self.title,
                width=self.WIDTH,
                format_image=self.FORMAT,
                quality_image=self.QUALITY
            )
        super(Image, self).save(*args, **kwargs)


class Feature(models.Model):
    """Модель характеристики товара."""

    WIDGET_TYPE = (
        ('CBX', 'checkbox'),
        ('SLC', 'select'),
        ('TXT', 'textfield')
    )

    title = models.CharField(
        max_length=200,
        verbose_name='характеристика'
    )
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        allow_unicode=False
    )

    widget_type = models.CharField(
        max_length=3,
        choices=WIDGET_TYPE,
        default='CBX',
        null=True,
        blank=True,
        verbose_name='тип виджета'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='активная характеристика'
    )
    objects = models.Manager()

    def save(self, *args, **kwargs):
        """Функция по созданию slug"""
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.title)
        super(Feature, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'app_features'
        ordering = ('title',)
        verbose_name = 'характеристика'
        verbose_name_plural = 'характеристики'


class FeatureValue(models.Model):
    value = models.CharField(
        max_length=200,
        verbose_name='значение характеристик'
    )
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        allow_unicode=False,
        verbose_name='slug'
    )
    feature = models.ForeignKey(
        'Feature',
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name='название характеристики'
    )

    objects = models.Manager()

    def __str__(self):
        return self.value

    def save(self, *args, **kwargs):
        """Функция по созданию slug"""
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.value)
        super(FeatureValue, self).save(*args, **kwargs)

    class Meta:
        db_table = 'app_values'
        ordering = ('value',)
        verbose_name = 'значение характеристик'
        verbose_name_plural = 'значения характеристик'

# class ItemImage(models.Model):
#     item = models.ForeignKey(
#         'Item',
#         on_delete=models.CASCADE,
#         related_name='images'
#     )
#     image = models.ForeignKey(
#         'Image',
#         on_delete=models.CASCADE
#     )
#     main = models.BooleanField(
#         default=False
#     )
#
#     class Meta:
#         db_table = 'app_items_image'
#         verbose_name_plural = 'изображения'
#
#     def __str__(self):
#         return self.pk
