from django.db import models
from django.contrib.auth.models import User

from app_store.managers.app_store_managers import StoreIsActiveManager
from utils.my_utils import slugify_for_cyrillic_text


class Store(models.Model):
    # TODO Store(models.Model) description
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
    delivery_fees = models.SmallIntegerField(default=0,
                                             verbose_name='стоимость доставки')
    min_free_delivery = models.IntegerField(default=0,
                                            verbose_name='минимальная сумма бесплатной доставки')
    owner = models.ForeignKey(User,
                              on_delete=models.SET_NULL,
                              null=True,
                              related_name='store',
                              verbose_name='собственник'
                              )
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='дата создания'
                                   )
    updated = models.DateTimeField(auto_now_add=True,
                                   verbose_name='дата обновления'
                                   )
    description = models.TextField(default='',
                                   blank=True,
                                   verbose_name='Описание магазина')
    logo = models.ImageField(upload_to='store/logo/',
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
