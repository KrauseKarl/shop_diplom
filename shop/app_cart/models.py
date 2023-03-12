from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User
from django.db.models import F, Q, Sum, QuerySet, Manager
from django.utils.timezone import now

from app_item.models import Item
from app_order.models import Order


class CartItem(models.Model):
    """Модель выбранного товара."""
    STATUS = (
        ('in_cart', 'в корзине'),
        ('not_paid', 'заказан'),
        ('new', 'новый'),
        ('in_progress', 'собирается'),
        ('on_the_way', 'доставляется'),
        ('is_ready', 'готов к выдаче'),
        ('completed', 'доставлен'),
        ('deactivated', 'отменен')
    )




    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='cart_item'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_add_items',
        verbose_name='покупатель',
        null=True
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='items_is_paid',
        verbose_name='заказ'
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
    is_paid = models.BooleanField(
        default=False,
        verbose_name='статус оплаты'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        verbose_name='статус выбранного товара'
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

    class Meta:
        db_table = 'app_items_in_cart'
        ordering = ['item']
        verbose_name = 'выбранный товар'

    def save(self, *args, **kwargs):
        self.total = self.total_price()
        self.updated = now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.quantity}шт. {self.item} в корзине'

    def total_price(self):
        """Стоимость выбранного товара."""
        return int(self.quantity * self.item.item_price)

    def get_store_title(self):
        """Возвращает название магазина."""
        return self.item.get_store

    @property
    def available(self):
        return self.item.filter(Q(is_available=True) & Q(stock__gt=0))


class Cart(models.Model):
    """Модель корзины."""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             null=True,
                             blank=True,
                             related_name='user_cart',
                             verbose_name='покупатель'
                             )
    items = models.ManyToManyField(
        CartItem,
        related_name='all_items',
        verbose_name='товар'
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name='корзина анонимного пользователя'
    )
    session_key = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name='ключ сессии'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name='корзина в архиве'
    )

    objects = models.Manager()

    class Meta:
        db_table = 'app_carts'
        ordering = ['created']
        verbose_name = 'корзина'
        verbose_name_plural = 'корзины'

    def __str__(self):
        return f'корзина №{self.pk}'

    @property
    def get_all_items(self):
        """Все доступные товары."""
        return self.items.select_related('item').filter(
            Q(is_paid=False) &
            Q(item__is_available=True) &
            Q(item__stock__gt=1)
        )

    @property
    def get_total_price(self):
        """Цена всей корзины."""
        if not self.is_empty():
            return self.get_all_items.aggregate(total=Sum(F('quantity') * F('price'))).get('total', 0)
        return 0

    @property
    def get_total_quantity(self):
        """Количество товаров в корзине."""
        return self.get_all_items.count()

    def is_empty(self):
        return True if self.get_total_quantity == 0 else False

    def clear(self):
        self.get_all_items.delete()

    def cart_serializable(self):
        cart_serialized = {}
        for product in self.get_all_items:
            data = {f'{product}': {
                'quantity': product.quantity,
                'total': product.total,
                'price': product.price,
                'item': product.item,
                'is_paid': product.is_paid,
            }
            }
            cart_serialized.update(data)
        return cart_serialized

#
# @receiver(post_save, sender=Cart)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Cart.objects.create(user=instance)


# @receiver(post_save, sender=Cart)
# def update_cart_receiver(sender, instance, **kwargs):
#     cache.get_or_set(f'cart_dict_{instance.pk}', default=instance)
#     instance.save()

# class CartManager(Manager):
#     def get_queryset(self):
#         return CartQuerySet(self.model, using=self._db)
#
#
# class CartQuerySet(QuerySet):
#     def update(self, request, **kwargs):
#         cache.delete(f'cart_dict_{request.user}')
#         super(CartQuerySet, self).update(updated=timezone.now(), **kwargs)
