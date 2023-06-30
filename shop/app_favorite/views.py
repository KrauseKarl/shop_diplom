from django.shortcuts import render, redirect
from django.views import generic

from app_favorite.favorites import Favorite
from app_item import models as item_models


class FavoriteAddItem(generic.TemplateView):
    """ Класс-представление для добавления товара в избранное"""

    model = item_models.Item

    def get(self, request, *args, **kwargs):
        Favorite(request).add(str(kwargs['pk']))
        return redirect(request.META.get('HTTP_REFERER'))


class FavoriteRemoveItem(generic.TemplateView):
    """ Класс-представление для удаления товара из корзины"""

    model = item_models.Item

    def get(self, request, *args, **kwargs):
        Favorite(request).remove(kwargs['pk'])
        return redirect(request.META.get('HTTP_REFERER'))


class FavoriteDetailView(generic.DetailView):
    """ Класс-представление для отображения избранных товаров."""

    model = item_models.Item
    template_name = 'app_favorite/favorites_list.html'

    def get(self, request, *args, **kwargs):
        """
        Функция-get для отображения корзины.
        возвращает на страницу корзины
        :return: корзину и id пользователя
        :rtype: dict
        """
        object_list = Favorite(request).all()
        value_list = object_list.values_list('feature_value', flat=True)
        compare_mode = bool(request.GET.get('compare'))
        if compare_mode:
            final_list = {}
            unique = []
            for val in value_list:
                final_list[val] = final_list.get(val, 0) + 1
            for k, v in final_list.items():
                if v < object_list.count():
                    try:
                        value = item_models.FeatureValue.objects.get(id=k)
                        if value.feature not in unique:
                            unique.append(value.feature)
                    except ValueError:
                        pass
        else:
            unique = item_models.Feature.objects.filter(values__in=value_list).distinct()
        context = {
            'object_list': object_list,
            'unique': unique
        }
        return render(request, self.template_name, context=context)


class CompareItemView(generic.DetailView):
    """ Класс-представление для отображения корзины корзины"""

    model = item_models.Item
    template_name = 'app_favorite/favoriets_list.html'
    queryset = item_models.Item.objects.all()

    def get(self, request, *args, **kwargs):

        favorites = request.session['favorites'].keys()
        favorites_id = [int(item) for item in favorites]
        queryset = self.queryset.filter(id__in=favorites_id)
        sort = None
        favorites = Favorite(request)
        context = {'favorites': queryset, 'order_by': sort}

        return render(request, self.template_name, context=context)


class FavoriteRemoveAll(generic.TemplateView):
    """ Класс-представление для удаления товара из корзины"""
    pass
    # model = Accommodation
    # template_name = 'favorites/favorites_detail.html'
    #
    # def post(self, request, *args, **kwargs):
    #     """
    #           Функция-post для удаления квартиры из избранного на странице квартиры.
    #           :return: возвращает на страницу корзины
    #           :rtype: dict
    #           """
    #     favorites = Favorite(request)
    #     favorites.clear()
    #     return redirect(reverse('app_favorites:detail_favorites'))
