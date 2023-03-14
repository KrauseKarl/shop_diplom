from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

from app_settings.models import SiteSettings
from app_store.models import Store


class Order(models.Model):
    """Модель заказа."""

    STATUS = (
        ('created', 'сформирован'),
        ('paid', 'оплачен'),
        ('on_the_way', 'доставляется'),
        ('is_ready', 'готов к выдаче'),
        ('completed', 'доставлен'),
        ('deactivated', 'отменен')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_order'
    )
    store = models.ManyToManyField(
        Store,
        related_name='orders',
        verbose_name='магазины'
    )
    name = models.CharField(
        max_length=250,
        verbose_name='имя получателя'
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='оплачен'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        verbose_name='статус заказа',
        default='created'
    )
    total_sum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='сумма заказа',
        default=0
    )
    delivery = models.CharField(
        max_length=20,
        choices=SiteSettings.DELIVERY,
        verbose_name='доставка'
    )
    delivery_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='сумма доставки',
        default=0
    )
    pay = models.CharField(
        max_length=20,
        choices=SiteSettings.PAY_TYPE,
        verbose_name='оплата'
    )
    email = models.EmailField(
        max_length=250,
        verbose_name='электронная почта'
    )
    telephone = models.CharField(
        max_length=20,
        verbose_name='телефон'
    )
    city = models.CharField(
        max_length=200,
        verbose_name='город'
    )
    address = models.CharField(
        max_length=200,
        verbose_name='адрес'
    )
    comment = models.TextField(
        verbose_name='Комментарий к заказу',
        null=True,
        blank=True
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата обновления'
    )
    error = models.CharField(
        max_length=200,
        default='',
        blank=True
    )

    objects = models.Manager()

    class Meta:
        db_table = 'app_order'
        ordering = ['created']
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def save(self, *args, **kwargs):
        self.updated = now()
        super().save(*args, **kwargs)

    # def get_order_total_sum(self):
    #     return self.items_is_paid.aggregate(total=Sum(F('quantity') * F('price'),
    #                                                   output_field=DecimalField())).get('total', 0)

    def __str__(self):
        return f'Заказ №{self.user.id:05}-{self.pk}'

    def get_quantity(self):
        return self.items_is_paid.count()

class Address(models.Model):
    """Модель адреса доставки."""
    city = models.CharField(
        max_length=200,
        verbose_name='город'
    )
    address = models.CharField(
        max_length=200,
        verbose_name='адрес'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='address'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата обновления'
    )
    objects = models.Manager()

    def __str__(self):
        return f'город: {self.city}, адрес: {self.address}'

    class Meta:
        db_table = 'app_post_address'
        ordering = ['-created']
        verbose_name = 'адрес'
        verbose_name_plural = 'адреса'
