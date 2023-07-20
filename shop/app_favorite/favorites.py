from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404

# models
from app_item import models as item_models


class Favorite:
    """Класс для создания и управления списка избранных товаров."""

    def __init__(self, request):
        """Инициализируем избранное."""
        self.session = request.session
        self.request = request
        favorites = self.session.get(settings.FAVORITE_SESSION_ID)
        if not favorites:
            favorites = self.session[settings.FAVORITE_SESSION_ID] = []
        self.favorites = favorites

    def add(self, item_pk):
        """Функция для добавления продукта в избранного."""
        item = get_object_or_404(item_models.Item, pk=item_pk)
        if self.favorites.__len__() < 100:
            if item_pk not in self.favorites:
                self.favorites.append(int(item_pk))
            self.save()
            messages.add_message(
                self.request, messages.SUCCESS, "товар добавлен в избранное"
            )
        else:
            messages.add_message(self.request, messages.WARNING, "Превышен лимит")

    def save(self):
        """Функция для обновление сессии избранного."""
        self.session[settings.FAVORITE_SESSION_ID] = self.favorites
        self.session.modified = True

    def remove(self, item_pk):
        """Удаление товара из избранного."""
        if item_pk in self.favorites:
            self.favorites.remove(item_pk)
            self.save()
            messages.add_message(
                self.request, messages.WARNING, "товар удален из избранного"
            )

    def __len__(self):
        """Функция для подсчет всех товаров в избранном."""
        return len(self.favorites)

    def clear(self):
        """Функция для удаление списка избранных товаров из сессии."""
        del self.session[settings.FAVORITE_SESSION_ID]
        self.session.modified = True

    def all(self):
        items = item_models.Item.objects.filter(id__in=self.favorites)
        return items
