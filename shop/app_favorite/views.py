from django.shortcuts import render
from django.views import generic, View


class FavoriteAddFlat(View):
    """ Класс-представление для добавления квартир в избранное"""
    pass
    # model = Accommodation
    # template_name = 'app_apartments/apartments_detail.html'
    #
    # def get(self, request, *args, **kwargs):
    #     favorites = Favorite(request)
    #     pk = kwargs['pk']
    #     flat = get_object_or_404(Accommodation, id=pk)
    #     favorites.add(flat=flat)
    #     return redirect(reverse('app_apartments:detail_apartment', args=[flat.pk]))
    #
    # @staticmethod
    # def post(request, *args, **kwargs):
    #     """
    #      Функция-post для создания корзины.
    #      Создает объект(запись) ('Cart')
    #      возвращает на страницу товара.
    #      в случае успешного добавления товара
    #      :return: форму, товар и сообщение об успешном добавлении
    #      в обратном случае
    #      :return: форму товар и сообщение об ошибки(недостаточно ед. товара)
    #      :rtype: dict
    #      """
    #     favorites = Favorite(request)
    #     pk = kwargs['pk']
    #     flat = get_object_or_404(Accommodation, id=pk)
    #     favorites.add(flat=flat)
    #     return redirect(reverse('app_apartments:detail_apartment', args=[flat.pk]))


class FavoriteRemoveFlat(generic.TemplateView):
    """ Класс-представление для удаления товара из корзины"""
    pass
    # model = Accommodation
    # template_name = 'app_apartments/apartments_detail.html'
    #
    # def get(self, request, *args, **kwargs):
    #     """
    #           Функция-get для удаления квартиры из списка избранных квартир.
    #           :return: возвращает на страницу корзины
    #           :rtype: dict
    #           """
    #     pk = kwargs['pk']
    #     favorites = Favorite(request)
    #     flat = get_object_or_404(Accommodation, id=pk)
    #     favorites.remove(flat)
    #     return redirect(reverse('app_apartments:detail_apartment', args=[flat.pk]))
    #     # return redirect('app_favorites:detail_favorites')
    #
    # def post(self, request, *args, **kwargs):
    #     """
    #           Функция-post для удаления квартиры из избранного на странице квартиры.
    #           :return: возвращает на страницу корзины
    #           :rtype: dict
    #           """
    #     pk = kwargs['pk']
    #     favorites = Favorite(request)
    #     flat = get_object_or_404(Accommodation, id=pk)
    #     favorites.remove(flat)
    #     return redirect(reverse('app_apartments:detail_apartment', args=[flat.pk]))


class FavoriteDetailView(generic.DetailView):
    """ Класс-представление для отображения корзины корзины"""
    pass
    # model = Accommodation
    # template_name = 'favorites/favorites_detail.html'
    #
    # def get(self, request, *args, **kwargs):
    #     """
    #     Функция-get для отображения корзины.
    #     возвращает на страницу корзины
    #     :return: корзину и id пользователя
    #     :rtype: dict
    #     """
    #     favorites = Favorite(request)
    #     context = {'favorites': favorites}
    #     return render(request, self.template_name, context=context)


class CompareView(generic.DetailView):
    """ Класс-представление для отображения корзины корзины"""
    pass
    # model = Accommodation
    # template_name = 'favorites/compare.html'
    # queryset = Accommodation.objects.all()
    #
    # def get(self, request, *args, **kwargs):
    #     """
    #     Функция-get для отображения корзины.
    #     возвращает на страницу корзины
    #     :return: корзину и id пользователя
    #     :rtype: dict
    #     """
    #
    #     query_set = ['quantity', 'price', 'square', 'floor']
    #     values_list = list((item, request.GET.get(item)) for item in query_set if request.GET.get(item))
    #     favorites = request.session['favorites'].keys()
    #     favorites_id = [int(flat) for flat in favorites]
    #     queryset = self.queryset.filter(id__in=favorites_id)
    #     sort = None
    #
    #     if values_list:
    #         if values_list[0][1] == 'up':
    #             order_by = f'{values_list[0][0]}'
    #         else:
    #             order_by = f'-{values_list[0][0]}'
    #         queryset = queryset.order_by(order_by)
    #         label_list = {
    #             'price': 'по возрастанию цены',
    #             '-price': 'по убыванию цены',
    #             'floor': 'по возрастанию этажности',
    #             '-floor': 'по убыванию этажности',
    #             'square': 'по возрастанию площади ',
    #             '-square': 'по убыванию площади',
    #         }
    #         if order_by in label_list.keys():
    #             sort = label_list[order_by]
    #     favorites = Favorite(request)
    #     context = {'favorites': queryset, 'order_by': sort}
    #
    #     return render(request, self.template_name, context=context)


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
