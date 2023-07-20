"""Модуль содержит все настроики для работы с корзиной в админке."""
from django.contrib import admin

from app_cart.models import Cart, CartItem


class CartItemAdmin(admin.ModelAdmin):
    """Класс для работы с тварами в админке."""

    list_display = ["id", "item", "quantity", "user", "is_paid", "cart"]
    list_filter = ("user", "is_paid", "cart")


class CartAdmin(admin.ModelAdmin):
    """Класс для работы с корзиной в админке."""

    list_display = ["id", "user", "is_anonymous", "created", "session_key"]
    list_filter = (
        "user",
        "is_anonymous",
        "session_key",
    )
    readonly_fields = ["user", "is_anonymous", "session_key"]
    exclude = [
        "items",
    ]


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
