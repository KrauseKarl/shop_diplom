from django.db import models

from app_cart.models import CartItem
from app_order.models import Order


class InvoiceItem(models.Model):
    """Модель оплаченного товара."""
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
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    objects = models.Manager()

    class Meta:
        db_table = 'app_invoice_item'
        ordering = ['-created']
        verbose_name = 'оплаченный товар'
        verbose_name_plural = 'оплаченный товары'


class Invoice(models.Model):
    """Модель чека оплаты заказа."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='чек'
    )
    total_purchase_sum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='сумма товаров',
        default=0
    )
    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='стоимость доставки',
        default=0
    )
    total_sum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='итоговая сумма',
        default=0
    )
    number = models.CharField(
        max_length=20,
        verbose_name='номер платежного документа'
    )
    paid_item = models.ManyToManyField(
        InvoiceItem,
        related_name='invoices',
        verbose_name='плаченный товар'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата создания'
    )
    objects = models.Manager()

    def __str__(self):
        return f'квитанция № {self.order.id:08}-{self.pk}'

    class Meta:
        db_table = 'app_invoices'
        ordering = ['-created']
        verbose_name = 'квитанция'
        verbose_name_plural = 'квитанции'
