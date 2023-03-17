from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, F
from django.utils.timezone import now

from app_cart.models import CartItem
from app_settings.models import SiteSettings
from app_store.models import Store


class OrderItem(models.Model):
    """Модель оплаченного товара."""
    STATUS = (
        ('not_paid', 'заказан'),
        ('paid', 'оплачен'),
        ('in_progress', 'собирается'),
        ('on_the_way', 'доставляется'),
        ('is_ready', 'готов к выдаче'),
        ('completed', 'доставлен'),
        ('deactivated', 'отменен')
    )
    item = models.ForeignKey(
        CartItem,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='cart_item'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='количество товара'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='цена товара'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая сумма'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        verbose_name='статус выбранного товара',
        default='in_cart'
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='order_items',
        verbose_name='заказ'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    objects = models.Manager()

    class Meta:
        db_table = 'app_order_item'
        ordering = ['-created']
        verbose_name = 'оплаченный товар'
        verbose_name_plural = 'оплаченный товары'

    def __str__(self):
        return f'Оплаченный товар {self.item}'

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        self.status = self.STATUS[0][0]
        super().save(*args, **kwargs)

class Order(models.Model):
    """Модель заказа."""

    STATUS = (
        ('created', 'сформирован'),
        ('paid', 'оплачен'),
        ('is_preparing', 'собирается'),
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
