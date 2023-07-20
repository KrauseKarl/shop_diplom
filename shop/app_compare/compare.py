"""Модуль содержит класс для создания и управления списка для сравнения."""
from django.conf import settings
from django.contrib import messages
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

# models
from app_item import models as item_models


class Comparison:
    """Класс для создания и управления списка товаров для сравнения."""

    def __init__(self, request):
        """Инициализируем товары для сравнения."""
        self.session = request.session
        self.request = request
        compare_items = self.session.get(settings.COMPARE_SESSION_ID)
        if not compare_items:
            compare_items = self.session[settings.COMPARE_SESSION_ID] = []
        self.compare_items = compare_items

    def add(self, item_pk):
        """Функция для добавления товаров для сравнения."""
        item = get_object_or_404(item_models.Item, pk=item_pk)

        if self.compare_items.__len__() > 0:
            first_item_category = self.first()
            if item.category == first_item_category:
                if self.compare_items.__len__() < 3:
                    if item_pk not in self.compare_items:
                        self.compare_items.append(int(item_pk))
                    self.save()
                    message_type = messages.SUCCESS
                    message_body = "товар добавлен в список среавнения"
                else:
                    message_type = messages.WARNING
                    message_body = "Превышен лимит для сравнения"
            else:
                message_type = messages.INFO
                message_body = f"""Товары должны быть из одной категории.
                Добавьте товар категории {first_item_category}.
                Или очистите список для сравнения.
                """
        else:
            if self.compare_items.__len__() < 3:
                if item_pk not in self.compare_items:
                    self.compare_items.append(int(item_pk))
                self.save()
                message_type = messages.SUCCESS
                message_body = "товар добавлен в список среавнения"
            else:
                message_type = messages.WARNING
                message_body = "Превышен лимит для сравнения"

        messages.add_message(self.request, message_type, message_body)

    def save(self):
        """Функция для обновление сессии товаров."""
        self.session[settings.COMPARE_SESSION_ID] = self.compare_items
        self.session.modified = True

    def remove(self, item_pk):
        """Удаление товара из списка для сравнения."""
        if item_pk in self.compare_items:
            self.compare_items.remove(item_pk)
            self.save()
            messages.add_message(
                self.request, messages.INFO, "товар удален из списка сравнения"
            )

    def __iter__(self):
        """Перебор элементов в списке и получение продуктов из базы данных."""
        items = item_models.Item.objects.filter(id__in=self.compare_items)
        for item in items:
            self.compare_items[str(item.id)]["compare_items"] = item

    def __len__(self):
        """Функция для подсчет всех товаров для сравнения."""
        return len(self.compare_items)

    def clear(self):
        """Функция для удаление списка товаров для сравнения из сессии."""
        del self.session[settings.COMPARE_SESSION_ID]
        self.session.modified = True

    def all(self) -> QuerySet:
        """Функция возвращает queryset всех товаров из списка."""
        items = item_models.Item.objects.filter(id__in=self.compare_items)
        return items

    def first(self):
        """Функция возвращает ПЕРВЫЙ товар."""
        item_id = self.compare_items[0]
        item_cat = item_models.Item.objects.filter(id=item_id).first().category
        return item_cat
