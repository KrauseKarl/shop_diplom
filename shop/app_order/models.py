from django.db import models
from django.contrib.auth.models import User

from app_store.models import Store


class Order(models.Model):
    # TODO Order(models.Model) description
    STATUS = (
        ('new', 'Новый'),
        ('in_progress', 'В обработке'),
        ('is_ready', 'Готов'),
        ('completed', 'Выполнен'),
        ('deactivated', 'Отменен')
    )
    DELIVERY = (
        ('express', 'экспресс'),
        ('standard', 'обычная'),
    )
    PAY_TYPE = (
        ('online', 'Онлайн картой'),
        ('someone', 'Онлайн со случайного чужого счета')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_order'
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='orders'
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
        verbose_name='статус заказа'
    )
    total_sum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='сумма заказа'
    )
    delivery = models.CharField(
        max_length=20,
        choices=DELIVERY,
        verbose_name='доставка'
    )
    pay = models.CharField(
        max_length=20,
        choices=PAY_TYPE,
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

    def __str__(self):
        return f'Заказ №{self.created.strftime("%Y%m%d-%H%M")}-{self.pk}'

    def get_quantity(self):
        return self.items_is_paid.count()


class Invoice(models.Model):
    # TODO Invoice(models.Model) description
    # DoesNotExist = None
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='чек'
    )
    recipient = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='all_store_invoices',
        verbose_name='магазин получатель'
    )
    number = models.CharField(
        max_length=20,
        verbose_name='номер карты'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    objects = models.Manager()

    def __str__(self):
        return f'квитанция №00{self.pk}-{self.order.id}'

    class Meta:
        db_table = 'app_invoices'
        ordering = ['-created']
        verbose_name = 'квитанция'
        verbose_name_plural = 'квитанции'
