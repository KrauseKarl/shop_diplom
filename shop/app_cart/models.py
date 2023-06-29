from django.db import models
from django.contrib.auth.models import User
from django.db.models import F, Q, Sum
from django.utils.timezone import now
from django.db.migrations import Migration
from app_item.models import Item
from app_settings.context_processors import load_settings
from app_settings.models import SiteSettings
from app_store.models import Store


class Cart(models.Model):
    """Модель корзины."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_cart',
        verbose_name='покупатель'
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
    updated = models.DateTimeField(
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
        return self.all_items.select_related('item').filter(
            Q(is_paid=False) &
            Q(item__is_available=True) &
            Q(item__stock__gt=1)
        )

    @property
    def get_total_price_with_discount(self):
        """Цена всей корзины."""
        if not self.is_empty():
            return sum(self.calculate_discount)
        return 0

    @property
    def get_total_price(self):
        if not self.is_empty():
            return self.all_items.select_related('item').\
                aggregate(total=Sum(F('quantity') * F('price'))).\
                get('total', 0)
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

    @property
    def total_cost_with_delivery(self):
        settings = SiteSettings.objects.get(id=1)
        min_free_delivery = settings .min_free_delivery
        delivery_fees = settings .delivery_fees
        if self.get_total_price_with_discount < min_free_delivery:
            return self.get_total_price_with_discount + float(delivery_fees)
        return self.get_total_price_with_discount

    @property
    def is_free_delivery(self):
        settings = SiteSettings.objects.get(id=1)
        min_free_delivery = settings.min_free_delivery
        delivery_fees = settings.delivery_fees
        if self.get_total_price_with_discount < min_free_delivery:
            return delivery_fees
        return 0

    @property
    def calculate_discount(self):
        price_list_with_discount = []
        cart_items = CartItem.objects.filter(cart=self)
        store_list = list(set(cart_items.values_list('item__store', flat=True).distinct()))
        for store_id in store_list:
            shop = Store.objects.values('min_for_discount', 'discount').get(id=store_id)
            items = CartItem.objects.filter(Q(item__store=store_id) & Q(cart=self))
            default_price = float(items.aggregate(Sum('total')).get('total__sum'))
            if default_price > float(shop.get('min_for_discount')):
                discount_price = round(default_price * ((100 - shop.get('discount')) / 100))
                price_list_with_discount.append(discount_price)
            else:
                price_list_with_discount.append(default_price)
        return price_list_with_discount


class CartItem(models.Model):
    """Модель выбранного товара."""
    STATUS = (
        ('in_cart', 'в корзине'),
        ('not_paid', 'заказан'),
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
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='all_items',
        verbose_name='покупатель',
        null=True,
        blank=True,
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

    @property
    def discount_price(self):
        """Стоимость выбранного товара с учетом скидки продавца."""
        shop = Store.objects.values('min_for_discount', 'discount').get(id=self.item.store.id)
        items = self.cart.all_items.filter(item__store=self.item.store.id)
        default_price = float(items.aggregate(Sum('total')).get('total__sum'))
        if default_price > float(shop.get('min_for_discount')):
            discount_price = round(float(self.price) * ((100 - shop.get('discount')) / 100))
        else:
            discount_price = self.price

        return int(self.quantity * discount_price)

    def get_store_title(self):
        """Возвращает название магазина."""
        return self.item.get_store

    @property
    def available(self):
        return self.item.filter(Q(is_available=True) & Q(stock__gt=0))




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
