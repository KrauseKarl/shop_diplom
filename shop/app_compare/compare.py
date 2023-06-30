from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404
# models
from app_item import models as item_models


class Comparison(object):
    """ Класс для создания и управления списка товаров для сравнения."""

    def __init__(self, request):
        """ Инициализируем товары для сравнения."""
        self.session = request.session
        self.request = request
        compare_items = self.session.get(settings.COMPARE_SESSION_ID)
        if not compare_items:
            compare_items = self.session[settings.COMPARE_SESSION_ID] = {}
        self.compare_items = compare_items

    def add(self, item_pk):
        """ Функция для добавления товаров для сравнения."""
        item = get_object_or_404(item_models.Item, pk=item_pk)
        if self.compare_items.__len__() > 0:
            first_item = self.all()[0]
            if first_item.category == item.category:
                if self.compare_items.__len__() < 3:
                    if item_pk not in self.compare_items:
                        self.compare_items[str(item)] = item.pk
                    self.save()
                    messages.add_message(self.request, messages.SUCCESS, 'товар добавлен в список среавнения')
                else:
                    messages.add_message(self.request, messages.WARNING, 'Превышен лимит для сравнения')
            else:
                messages.add_message(self.request, messages.WARNING, 'Товары должны быть из одной категории. ')
                messages.add_message(self.request, messages.INFO,
                f'Добавьте товар категории {first_item.category} или очистите список для сравнения')
        else:
            if self.compare_items.__len__() < 3:
                if item_pk not in self.compare_items:
                    self.compare_items[str(item)] = item.pk
                self.save()
                messages.add_message(self.request, messages.SUCCESS, 'товар добавлен в список среавнения')
            else:
                messages.add_message(self.request, messages.WARNING, 'Превышен лимит для сравнения')


    def save(self):
        """ Функция для обновление сессии товаров."""
        self.session[settings.COMPARE_SESSION_ID] = self.compare_items
        self.session.modified = True

    def remove(self, item_pk):
        """ Удаление товара из списка для сравнения."""
        item = get_object_or_404(item_models.Item, pk=item_pk)
        if item_pk in self.compare_items.values():
            del self.compare_items[str(item)]
            self.save()
            messages.add_message(self.request, messages.INFO, 'товар удален из списка сравнения')

    def __iter__(self):
        """ Перебор элементов в списке и получение продуктов из базы данных."""
        item_ids = self.compare_items.keys()
        items = item_models.Item.objects.filter(id__in=item_ids)
        for item in items:
            self.compare_items[str(item.id)]['compare_items'] = item

    def __len__(self):
        """ Функция для подсчет всех товаров для сравнения."""
        return len(self.compare_items)

    def clear(self):
        """ Функция для удаление списка товаров для сравнения из сессии."""
        del self.session[settings.COMPARE_SESSION_ID]
        self.session.modified = True

    def all(self):
        """  Функция возвращает все товары из списка. """
        item_id_list = [i for i in self.compare_items.values()]
        items = item_models.Item.objects.filter(id__in=item_id_list)
        return items
