from urllib.parse import urlencode
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from urllib.parse import parse_qs
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from app_item.models import Item, Category, Comment
from app_item.forms import CommentForm
from app_store.models import Store
from utils.my_utils import MixinPaginator, query_counter
from app_cart.services.cart_services import get_items_in_cart, get_current_cart, get_cart_item_in_cart
from app_item.services.comment_services import CommentHandler
from app_item.services.item_services import (
    AddItemToReview,
    get_colors,
    CategoryHandler,
    TagHandler, CountView, ItemHandler
)



class CategoryListView(ListView, MixinPaginator):
    """Класс-представление для отображения списка всех товаров по категориям."""
    model = Item
    paginate_by = 8
    queryset = Item.objects.all()

    @query_counter
    def get(self, request, category=None, **kwargs):
        super().get(request, **kwargs)
        """
        Функция возвращает queryset-товаров, queryset-тегов, словарь с цветами.
        отсортированный по выбранному параметру или все товары.
        :param category: категория товаров
        :return: response.
        """
        color = None
        #  создаем словарь всех параметров GET-запроса
        query_get_param_dict = ItemHandler.make_get_param_dict(self.request)

        #  фильтруем товары по переданной категории
        filter_items_by_category = CategoryHandler.filter_items_by_category(self.queryset, category)

        #  находим экземпляр класса Category по slug
        category = CategoryHandler.get_categories(category)

        #  фильтруем товары по всем остальным параметрам переданных в GET-запросе используя ранее созданных словарь
        object_list = ItemHandler.smart_filter(self.request, filter_items_by_category, query_get_param_dict)

        #  определяем диапазон цен в выбранной категории товаров
        if not object_list.exists():
            price_min_in_category, price_max_in_category = ItemHandler.get_range_price(filter_items_by_category)
        else:
            price_min_in_category, price_max_in_category = ItemHandler.get_range_price(object_list)
        if request.GET.get('price'):
            price_range = request.GET.get('price', None)
            price_min = int(price_range.split(';')[0])
            price_max = int(price_range.split(';')[1])
        else:
            price_min, price_max = price_min_in_category, price_max_in_category

        #   формируем сообщение по типе фильтрации
        sort_message = f'по категории {category}'

        # 5  формируем список из связанных категорий или дочерних категорий
        related_category_list = CategoryHandler.get_related_category_list(object_list)

        #  формируем список  всех доступных цветов
        set_colors = get_colors(object_list)

        #   формируем queryset 10 самых популярных тегов
        set_tags = TagHandler.get_tags_queryset(object_list)

        #   сортируем полученный queryset по GET-параметру 'order_by'
        if request.GET.get('order_by'):
            object_list = ItemHandler.ordering_items(queryset=object_list, order_by=request.GET.get('order_by'))
            sort_message = ItemHandler.ordering_message(sort_param=request.GET.get('order_by'))

        #   пагинация результата
        queryset = self.my_paginator(object_list, self.request, self.paginate_by)
        context = {
            'related_category_list': related_category_list,  # все категории в которых есть искомое слово
            'category': category,  # одна выбранная категория товара  (при GET-запросе)
            'set_tags': set_tags,  # 10 тегов
            'color': color,  # один(несколько) выбранный(х) (при GET-запросе)  цвет(ов)
            'set_colors': set_colors,  # набор цветов доступных в queryset  товаров
            'object_list': queryset,  # queryset товаров
            'price_min_in_category': price_min_in_category,
            'price_max_in_category': price_max_in_category,
            'price_min': price_min,  # минимальная выбранная (при GET-запросе) цена товаров
            'price_max': price_max,  # максимальная выбранная (при GET-запросе)  цена товаров
            'sort_message': sort_message,  # сообщение (вид сортировки, фильтрации и результат)
            'get_params': query_get_param_dict  # словарь из всех параметров GET-запроса
        }
        return render(request, 'app_item/item_list.html', context=context)


class TagListView(ListView, MixinPaginator):
    """Класс-представление для отображения списка всех товаров по тегам."""
    model = Item
    template_name = 'app_item/item_list.html'
    queryset = ItemHandler.get_popular_items()
    paginate_by = 6

    @query_counter
    def get(self, request,  tag=None, *args, **kwargs):
        super(TagListView, self).get(request, *args, **kwargs)

        #  фильтруем товары по переданному тегу
        object_list = TagHandler.filter_queryset_by_tag(self.queryset, tag=tag)

        # формируем список из связанных категорий или дочерних категорий
        related_category_list = CategoryHandler.get_related_category_list(object_list)

        #  находим экземпляр класса Tag по slug
        tag = TagHandler.get_tag(tag)

        #   формируем сообщение по типе фильтрации
        sort_message = f'по тегу {tag}'

        #  формируем список из связанных тегов
        set_tags = TagHandler.get_tags_queryset(object_list)

        # 9  сортируем полученный queryset по GET-параметру 'order_by'
        if request.GET.get('order_by'):
            sort_param = request.GET.get('order_by')
            object_list = ItemHandler.ordering_items(queryset=object_list, order_by=sort_param)
            sort_message = ItemHandler.ordering_message(sort_param=sort_param)
        # 10  пагинация результата
        queryset = self.my_paginator(object_list, self.request, self.paginate_by)  # пагинация результата

        context = {
            'related_category_list': related_category_list,  # все категории в которых есть тег
            'tag': tag,  # один выбранный тег (при GET-запросе)
            'set_tags': set_tags,  # связанные теги
            'object_list': queryset,  # queryset товаров
            'sort_message': sort_message,  # сообщение (вид сортировки, фильтрации и результат)
        }
        return render(request, 'app_item/item_list.html', context=context)


class FilterListView(ListView, MixinPaginator):
    """Класс-представление для отображения отфильтрованных товаров."""
    model = Item
    paginate_by = 8
    template_name = 'app_item/item_list.html'
    queryset = Item.objects.all()

    @query_counter
    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        object_list = self.queryset
        query_get_param_dict = ItemHandler.make_get_param_dict(self.request)
        object_list = ItemHandler.smart_filter(self.request, object_list, query_get_param_dict)
        related_category_list = CategoryHandler.get_related_category_list(object_list)
        # if self.request.GET.get('q'):
        #     # получаем значение для поиска и удаляем последний символ
        #     query = str(self.request.GET.get('q'))  # [:-1]
        #     # первый символ значения  к верхнему регитсру
        #     title = query.title()
        #     # всю строку значения к нижнему регистру
        #     lower = query.lower()
        #     # ищем товар по вхождению в названии категорий, в названии товаров, или в названии тегов
        #     object_list = object_list.select_related('category').filter(
        #         Q(category__title__icontains=title) |
        #         Q(title__icontains=title) |
        #         Q(tag__title__icontains=title) |
        #         Q(category__title__icontains=lower) |
        #         Q(title__icontains=lower) |
        #         Q(tag__title__icontains=lower) |
        #         Q(store__title__icontains=lower)
        #     ).distinct()
        #     #  формируем список из связанных товаров
        #     related_items = Category.objects.filter(items__in=object_list).values_list('id', flat=True).distinct()
        #     #  фильтруем товары по списку связанных товаров
        #     object_list = self.queryset.filter(category__in=related_items)
        # if self.request.GET.get('price', None):
        #     price = self.request.GET.get('price').split(';')
        #     price_min = int(price[0])
        #     price_max = int(price[1])
        #     queryset = object_list.filter(price__range=(price_min, price_max))
        #
        # if self.request.GET.getlist('color', None):
        #     color = self.request.GET.getlist('color')
        #     object_list = object_list.exclude(color=None).filter(color__in=color)

        if request.GET.get('order_by'):
            sort_by = request.GET.get('order_by')
            object_list = ItemHandler.ordering_items(queryset=object_list, order_by=sort_by)
        sort_message = ItemHandler.ordering_message(sort_param=request.GET.get('order_by'))
        #  формируем список  всех доступных цветов
        set_colors = get_colors(object_list)
        #  формируем queryset 10 самых популярных тегов
        set_tags = TagHandler.get_tags_queryset(object_list)  # для отображения 10 самых популярных тегов

        object_list = self.my_paginator(object_list, self.request, self.paginate_by)  # пагинация результата
        context = {
            'object_list': object_list,
            'sort_message': sort_message,
            'set_colors': set_colors,
            'set_tags': set_tags,
            'related_category_list': related_category_list,
            }
        return render(request, self.template_name, context=context)

    # def get_context_data(self, *, object_list=None, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     items = self.get_queryset()
    #     queryset = self.my_paginator(items, self.request, self.paginate_by)
    #     context['object_list'] = queryset
    #     if self.request.GET.getlist('color', None):
    #         context['colors'] = self.request.GET.getlist('color', None)
    #     else:
    #         context['colors'] = get_colors(items)
    #     context['range_price'] = ItemHandler.get_range_price(queryset.object_list)
    #     context['sort_message'] = items.count()
    #     return context


class ItemDetail(DetailView, CreateView):
    """Класс-представление для отображения одного товара."""
    model = Item
    context_object_name = 'item'
    template_name = 'app_item/item_detail.html'
    form_class = CommentForm
    success_url = '/'

    @query_counter
    def get(self, request, *args, **kwargs):
        """
        Get-функция для отображения одного товара.
        Добавляет товар к списку просмотренных товаров пользователя
        и добавляет IP-адрес пользователя к товару.
        """
        item = self.get_object()
        user = request.user
        form = self.get_form()

        # добавляет товар в список просмотренных товаров пользователя
        try:
            AddItemToReview().add_item_to_review(user=user, item_id=item.id)
        except ObjectDoesNotExist:
            pass
        # увеличивает количество просмотров товара
        CountView().add_view(request, item_id=item.id)

        # список всех тегов товара
        tags = TagHandler.get_tags_queryset(item_id=item.id)

        # список всех  товаров (Item) в корзине
        item_in_cart = get_items_in_cart(self.request)

        # список всех добавленных товаров (CartItem) в корзине
        cart_item_in_cart = get_cart_item_in_cart(self.request, item)

        # количество всех добавленных в корзину товаров (CartItem)
        try:
            cart_item_in_cart_quantity = cart_item_in_cart.quantity
        except (AttributeError, ObjectDoesNotExist):
            cart_item_in_cart_quantity = 0

        # общее кол-во комментариев(прошедших модерацию) к товару
        comments_count = CommentHandler.get_comment_cont(item.id)

        # все характеристики товара отсортированные по названию характеристик
        features = item.feature_value.order_by('feature__title')
        context = {
            'form': form,                                        # форма для создания комментария к товару
            'tags': tags,                                        # список тегов товара
            'item': item,                                        # товар (экземпляр класса Item)
            'features': features,                                # список характеристик товара
            'comments_count': comments_count,                    # счетчик кол-ва комментариев(прошедших модерацию)
            'already_in_cart': item_in_cart,                     # все товары (Item) который присутствуют в корзине
            'already_in_cart_count': cart_item_in_cart_quantity  # кол-во всех товаров добавленных (CartItem) в корзину
        }
        return self.render_to_response(context)

    def form_valid(self, form):
        """
        Функция для создания комментария о товаре.
        :param form: форма для создания комментария
        :return: на страницу товара
        """
        item = self.kwargs['pk']
        user = self.request.user
        data = self.request.POST
        CommentHandler.add_comment(user=user, item_id=item, data=data)
        messages.add_message(self.request, messages.SUCCESS,
                             f"{user.get_full_name()}, спасибо за комментарий. После модерации он будет опубликован.")
        return redirect(self.request.get_full_path())

    def get_success_url(self):
        messages.add_message(self.request, messages.ERROR,
                             "Ошибка.Комментарий не был добавлен.Повторите отправку комментария.")
        return reverse('app_item:item_detail', args=[self.request.pk])


class ItemBestSellerList(ListView):
    """Класс-представление для отображения списка всех товаров отсортированных по продажам."""
    model = Item
    template_name = 'app_item/best_seller_list.html'
    queryset = ItemHandler.get_bestseller()
    paginate_by = 12


class ItemNewList(ListView):
    """Класс-представление для отображения списка всех новых товаров."""
    model = Item
    template_name = 'app_item/new_items.html'
    queryset = ItemHandler.get_new_item_list()
    paginate_by = 12


class ItemForYouList(ListView, MixinPaginator):
    """Класс-представление для отображения  всех товаров, подходящих для покупателя."""
    model = Item
    template_name = 'app_item/items_for_you.html'
    paginate_by = 8

    @query_counter
    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        queryset = ItemHandler.get_items_for_you(self.request)
        object_list = self.my_paginator(queryset, self.request, self.paginate_by)
        context = {'object_list': object_list}
        return render(request, self.template_name, context=context)


class StoreItemList(DetailView, MixinPaginator):
    """Класс-представление для отображения  всех товаров, подходящих для покупателя."""
    model = Store
    template_name = 'app_item/item_list.html'
    context_object_name = 'store'
    paginate_by = 8

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        store = self.get_object()
        object_list = store.items.all()
        related_category_list = CategoryHandler.get_related_category_list(object_list)
        sort_message = f'товары магазина { store }'
        if request.GET.get('order_by'):
            object_list = ItemHandler.ordering_items(queryset=object_list, order_by=request.GET.get('order_by'))
            sort_message = ItemHandler.ordering_message(sort_param=request.GET.get('order_by'))
        object_list = self.my_paginator(object_list, self.request, self.paginate_by)

        context = {
            'object_list': object_list,
            'related_category_list': related_category_list,
            'store': store,
            'sort_message': sort_message,
        }
        return render(request, self.template_name, context=context)


class DeleteComment(DetailView):
    """Класс-представление для удаления комментария."""
    model = Item
    template_name = 'app_item/item_detail.html'
    context_object_name = 'item'

    def get(self, request, *args, **kwargs):
        """
        Функция удаляет комментарий о товаре.
        :return: возвращает на страницу товара
        """

        item = kwargs['pk']
        comment = kwargs['comment_id']
        user = request.user
        CommentHandler.delete_comment(user=user, comment_id=comment, item_id=item)
        messages.add_message(self.request, messages.INFO, "Комментарий удален.")
        return redirect('app_item:item_detail', item)


class EditComment(UpdateView):
    """Класс-представление для редактирования комментария."""
    model = Comment
    context_object_name = 'comments'
    template_name = 'app_item/comment_edit.html'
    form_class = CommentForm

    def get(self, request, *args, **kwargs):
        """GET-функция для редактирования комментария."""
        comment_id = kwargs['comment_id']
        comment = Comment.objects.filter(id=comment_id)[0]
        form = CommentForm(instance=comment)
        return render(request, self.template_name, {'form': form, 'comments': comment})

    def post(self, request, *args, **kwargs):
        """POST-функция для редактирования комментария."""
        comment_id = kwargs['comment_id']
        comment = Comment.objects.get(id=comment_id)
        form = CommentForm(request.POST, instance=comment)
        item_id = kwargs['pk']

        if form.is_valid():
            comment.is_published = False
            comment.save(force_update=True)
            messages.add_message(self.request, messages.SUCCESS,
                                 "Комментарий изменен.После модерации он будет опубликован.")
            return redirect('app_item:item_detail', item_id)
        return render(request, self.template_name, {'form': form, 'comments': comment})


def remove_param(request, param):
    """Функция для удаления параметров фильтра в строке-запроса."""
    query_string = request.META.get('HTTP_REFERER').split('?')
    query_string_dict = parse_qs(query_string[1])
    for key_param, value_param in query_string_dict.items():
        if param == key_param:
            if len(query_string_dict[key_param]) > 1:
                query_string_dict[key_param].remove(param)
                break
            else:
                del query_string_dict[key_param]
                break

    for key, value in query_string_dict.items():
        for index, value_param in enumerate(value):
            if param in value_param:
                value.pop(index)
                query_string_dict[key] = value
    path = urlencode(query_string_dict, True)
    if path:
        result = query_string[0] + '?' + path
    else:
        result = query_string[0]
    return redirect(result)
