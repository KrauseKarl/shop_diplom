from django.conf import settings

from app_apartments.models import Accommodation


class Favorite(object):
    """ Класс для создания и управления корзиной."""

    def __init__(self, request):
        """ Инициализируем избранное."""
        self.session = request.session
        favorites = self.session.get(settings.FAVORITE_SESSION_ID)
        if not favorites:
            favorites = self.session[settings.FAVORITE_SESSION_ID] = {}
        self.favorites = favorites

    def add(self, flat):
        """ Функция для добавления продукта в корзину или обновления его количество."""
        flat_id = str(flat.id)
        flat = Accommodation.objects.get(id=flat_id)
        if flat_id not in self.favorites:
            self.favorites[flat_id] = flat
        self.save()

    def save(self):
        """ Функция для обновление сессии cart."""
        self.session[settings.FAVORITE_SESSION_ID] = self.favorites
        self.session.modified = True

    def remove(self, flat):
        """Удаление товара из корзины."""
        flat_id = str(flat.id)
        if flat_id in self.favorites:
            del self.favorites[flat_id]
            self.save()

    def __iter__(self):
        """ Перебор элементов в корзине и получение продуктов из базы данных."""
        flat_ids = self.favorites.keys()

        flats = Accommodation.objects.filter(id__in=flat_ids)
        for flat in flats:
            self.favorites[str(flat.id)]['flat'] = flat

    def __len__(self):
        """ Функция для подсчет всех товаров в корзине."""
        return len(self.favorites)

    def clear(self):
        """Функция для удаление корзины из сессии."""
        del self.session[settings.FAVORITE_SESSION_ID]
        self.session.modified = True
