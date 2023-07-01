from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404
# models
from app_item import models as item_models


class Favorite:
    """ Класс для создания и управления списка избранных товаров."""

    def __init__(self, request):
        """ Инициализируем избранное."""
        self.session = request.session
        self.request = request
        favorites = self.session.get(settings.FAVORITE_SESSION_ID)
        if not favorites:
            favorites = self.session[settings.FAVORITE_SESSION_ID] = {}
        self.favorites = favorites

    def add(self, item_pk):
        """ Функция для добавления продукта в избранного."""
        item = get_object_or_404(item_models.Item, pk=item_pk)
        if self.favorites.__len__() < 100:
            if item_pk not in self.favorites:
                self.favorites[str(item)] = item.pk
            self.save()
            messages.add_message(self.request, messages.SUCCESS, 'товар добавлен в избранное')
        else:
            messages.add_message(self.request, messages.WARNING, 'Превышен лимит')

    def save(self):
        """ Функция для обновление сессии избранного."""
        self.session[settings.FAVORITE_SESSION_ID] = self.favorites
        self.session.modified = True

    def remove(self, item_pk):
        """Удаление товара из избранного."""
        item = get_object_or_404(item_models.Item, pk=item_pk)
        if item_pk in self.favorites.values():
            del self.favorites[str(item)]
            self.save()
            messages.add_message(self.request, messages.WARNING, 'товар удален из избранного')

    def __iter__(self):
        """ Перебор элементов в избранном и получение продуктов из базы данных."""
        item_ids = self.favorites.keys()
        items = item_models.Item.objects.filter(id__in=item_ids)
        for item in items:
            self.favorites[str(item.id)]['favorite_item'] = item

    def __len__(self):
        """ Функция для подсчет всех товаров в избранном."""
        return len(self.favorites)

    def clear(self):
        """Функция для удаление списка избранных товаров из сессии."""
        del self.session[settings.FAVORITE_SESSION_ID]
        self.session.modified = True

    def all(self):
        item_id_list = [i for i in self.favorites.values()]
        items = item_models.Item.objects.filter(id__in=item_id_list)
        return items
