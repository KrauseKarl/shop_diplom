from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.urls import reverse

from app_store.managers.app_store_managers import StoreIsActiveManager
from utils.my_utils import slugify_for_cyrillic_text


class Store(models.Model):
    """  Модель магазина."""
    title = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='название магазина'
    )
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        allow_unicode=False,
        verbose_name='slug'
    )
    discount = models.SmallIntegerField(
        default=0,
        verbose_name='скидка',
        validators=[
            MaxValueValidator(99),
            MinValueValidator(0)
        ]
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='store',
        verbose_name='собственник'
    )
    min_for_discount = models.DecimalField(
        decimal_places=2,
        max_digits=9,
        default=0,
        verbose_name='минимальная сумма бесплатной доставки'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата обновления'
    )
    description = models.TextField(
        default='',
        blank=True,
        verbose_name='Описание магазина')
    logo = models.ImageField(
        upload_to='store/logo/',
        default='default_images/default_store.jpg',
        blank=True
    )
    is_active = models.BooleanField(default=False)

    objects = models.Manager()
    active_stores = StoreIsActiveManager()

    class Meta:
        db_table = 'app_store'
        ordering = ['created']
        verbose_name = 'магазин'
        verbose_name_plural = 'магазины'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Функция по созданию slug."""
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.title)
        super(Store, self).save(*args, **kwargs)

    def get_active(self):
        self.is_active = True
        return self.is_active

    def get_absolute_url(self):
        return reverse("app_item:store_list", kwargs={'slug': self.slug})

    @property
    def store_items(self):
        return self.items.all()

    @property
    def all_orders(self):
        return self.orders.count()

    @property
    def cash(self):
        return self.items.values_list('cart_item', flat=True).aggregate(total=Sum('cart_item__total')).get('total')

    @property
    def paid_item(self):
        return self.items.values_list('cart_item', flat=True).aggregate(total=Count('cart_item')).get('total')
