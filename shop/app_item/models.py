from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MinLengthValidator
from django.utils.timezone import now

from utils.my_utils import slugify_for_cyrillic_text
from app_store.models import Store
from app_item.managers.app_item_managers import (AvailableItemManager, UnavailableItemManager,
                                                 LimitedEditionManager, CategoryWithItemsManager,
                                                 ModeratedCommentsManager)


class IpAddress(models.Model):
    ip = models.CharField(max_length=15)

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
    MAGENTA = ' magenta'
    WHITE = 'white'
    BLACK = 'black'
    GREY = 'grey'

    COLOURS = (
        (RED, 'red'),
        (ORANGE, 'orange'),
        (YELLOW, 'yellow'),
        (GREEN, 'green'),
        (BLUE, 'blue'),
        (MAGENTA, 'magenta'),
        (WHITE, 'white'),
        (BLACK, 'black'),
        (GREY, 'grey'),
    )
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
    image = models.ManyToManyField(
        'Image',
        related_name='item_images',
        verbose_name='изображение'
    )
    tag = models.ManyToManyField(
        'Tag',
        max_length=20,
        blank=True,
        related_name='item_tags',
        verbose_name='тег'
    )

    features = models.ManyToManyField(
        'Feature',
        max_length=20,
        blank=True,
        related_name='item_features',
        verbose_name='характеристики'
    )

    objects = models.Manager()
    available_items = AvailableItemManager()
    unavailable_items = UnavailableItemManager()
    limited_items = LimitedEditionManager()

    class Meta:
        db_table = 'app_items'
        ordering = ['created']
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.title

    def get_price(self):
        """Функция возвращает цену товара."""
        return self.price

    @property
    def main_image(self):
        return self.image.first().image.url

    def get_absolute_url(self):
        return reverse('app_item:item_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        """Функция по созданию slug"""
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.title)
        self.updated = now()
        super(Item, self).save(*args, **kwargs)

    def total_views(self):
        """Функция возвращает общее количество просмотров для товара."""
        return self.views.count()

    @property
    def item_price(self):
        return self.price

    @property
    def get_store(self):
        return self.store



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

    objects = CategoryWithItemsManager()

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

    # @property
    # def url(self):
    #     module_name = self.__module__.split('.')[0].lower()
    #     class_name = self.__class__.__name__.lower()
    #     return f'{module_name}/?{class_name}={self.slug}'

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
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата обновления'
    )

    objects = models.Manager()
    published_comments = ModeratedCommentsManager()

    def __str__(self):
        return self.review[:15]

    class Meta:
        db_table = 'app_comments'
        ordering = ['-created_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'


class Image(models.Model):
    """Модель изображения."""
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
        default='static/img/default_flat.jpg',
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


class Feature(models.Model):
    """Модель характеристики товара."""
    title = models.CharField(
        max_length=200,
        verbose_name='характеристика'
    )
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        allow_unicode=False
    )

    value = models.CharField(
        max_length=200,
        verbose_name='значение'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='активная характеристика'
    )
    objects = models.Manager()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'app_features'
        ordering = ('title',)
        verbose_name = 'характеристика'
        verbose_name_plural = 'характеристики'

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
