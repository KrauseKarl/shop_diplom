"""Модуль содержит модель Магазина."""
import os

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.urls import reverse

from app_store.managers.app_store_managers import StoreIsActiveManager
from utils.my_utils import slugify_for_cyrillic_text


class Store(models.Model):
    """Модель магазина."""

    DEFAULT_IMAGE = "default_images/store.png"

    title = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name="название магазина"
    )
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        allow_unicode=False,
        verbose_name="slug"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="store",
        verbose_name="собственник",
    )
    discount = models.SmallIntegerField(
        default=0,
        verbose_name="скидка",
        validators=[MaxValueValidator(99), MinValueValidator(0)],
    )
    min_for_discount = models.IntegerField(
        default=0,
        verbose_name="минимальная сумма для бесплатной доставки",
        validators=[MinValueValidator(0)],
    )
    description = models.TextField(
        default="",
        blank=True,
        verbose_name="Описание магазина"
    )
    logo = models.ImageField(
        upload_to="store/logo/",
        default="default_images/default_store.jpg",
        blank=True
    )
    is_active = models.BooleanField(default=False)
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="дата создания"
    )
    updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name="дата обновления"
    )

    objects = models.Manager()
    active_stores = StoreIsActiveManager()

    class Meta:
        db_table = "app_store"
        ordering = ["title", "created"]
        verbose_name = "магазин"
        verbose_name_plural = "магазины"

    def __str__(self):
        """Метод для отображения информации об объекте класса Store."""
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_for_cyrillic_text(self.title)
        super(Store, self).save(*args, **kwargs)

    @property
    def get_logo(self):
        """
        Метод возвращает URL-изображения категории.

        Возвращает URL-изображения
        или дефолтное изображение.
        """
        if self.logo:
            return os.path.join(settings.MEDIA_URL, self.logo.url)
        else:
            return os.path.join(settings.MEDIA_URL, self.DEFAULT_IMAGE)

    def get_absolute_url(self):
        """Метод возвращает абсолютный путь до магазина."""
        return reverse("app_item:store_list", kwargs={"slug": self.slug})

    @property
    def store_items(self):
        """Метод возвращает все товары магазина."""
        return self.items.all()

    @property
    def all_orders(self):
        """Метод возвращает все заказы магазина."""
        return self.orders.count()

    @property
    def cash(self):
        """Метод возвращает сумму всех заказов."""
        return (
            self.orders.filter(order_items__item__item__store=self.id)
            .aggregate(total=Sum("order_items__item__total"))
            .get("total")
        )

    @property
    def paid_item(self):
        """Метод возвращает кол-во всех заказов."""
        return (
            self.orders.filter(order_items__item__item__store=self.id)
            .aggregate(total=Sum("order_items__quantity"))
            .get("total")
        )
