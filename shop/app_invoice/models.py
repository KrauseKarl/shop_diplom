from django.db import models

from app_order.models import Order, OrderItem


class Invoice(models.Model):
    """Модель чека оплаты заказа."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="invoices", verbose_name="заказ"
    )
    total_purchase_sum = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="сумма товаров", default=0
    )
    delivery_cost = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="стоимость доставки", default=0
    )
    total_sum = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="итоговая сумма", default=0
    )
    number = models.CharField(max_length=20, verbose_name="номер платежного документа")
    paid_item = models.ManyToManyField(
        OrderItem, related_name="invoice_item", verbose_name="оплаченный товар"
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="дата создания")
    objects = models.Manager()

    def __str__(self):
        return f"квитанция № {self.order.id:08}-{self.pk}"

    class Meta:
        db_table = "app_invoices"
        ordering = ["-created"]
        verbose_name = "квитанция"
        verbose_name_plural = "квитанции"
