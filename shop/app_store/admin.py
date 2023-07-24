"""Модуль содержит все настроики для работы с магазинами в админке."""
from django.contrib import admin
from django.utils.safestring import mark_safe

from app_store.models import Store


class StoreAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "owner",
        "full_image",
        "discount",
        "min_for_discount"
    ]
    readonly_fields = ["full_image", "owner"]

    def full_image(self, obj):
        """Метод возвращает ссылку на изображение логотипа."""
        return mark_safe(f'<img src="{obj.logo.url}" width=80/>')


admin.site.register(Store, StoreAdmin)
