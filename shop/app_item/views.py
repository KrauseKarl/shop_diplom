from urllib.parse import urlencode
from django.core.exceptions import ObjectDoesNotExist
from urllib.parse import parse_qs
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView

from app_item.models import (
    Item,
    Category,
    Comment,
    Tag)
from app_item.forms import CommentForm
from utils.my_utils import MixinPaginator
from app_cart.services.cart_services import get_items_in_cart
from app_item.services.comment_services import CommentHandler
from app_item.services.item_services import (
    AddItemToReview,
    get_colors,
    CategoryHandler,
    TagHandler, CountView, ItemHandler
)


class ItemList(ListView, MixinPaginator):
    """Класс-представление для отображения списка всех товаров."""
    model = Item
    template_name = 'app_item/item_list.html'
    queryset = ItemHandler.get_popular_items()
    paginate_by = 6

    def get(self, request, category=None, tag=None, order_by=None, color=None, q=None, **kwargs):
        super().get(request, **kwargs)

        """
        Функция возвращает queryset-товаров
        отсортированный по выбранному параметру или все товары.
        :param category: категория товаров
        :param tag: тег товаров
        :param order_by: сортировка по цене, популярности, новизне
        :param color: цвет товаров
        :return: Возвращает queryset-товаров,queryset-тегов, словарь с цветами.
        """
        sort_message = None
        color = None
        price_min = 0
        price_max = 0
        object_list = self.queryset
        all_colors_set = object_list
        filter_dict = {
            'order_by': 'отсортировано',
            'price': 'цена',
            'color': 'цвет',
            'title': 'название'
        }
        sort_dict = {
            '-price': 'сначала дороже',
            'price': 'сначала дешевле',
            'best_seller': ' не популярные',
            '-best_seller': 'популярные',
            '-created': 'новинки',
            'by_comments': 'по комментариям'
        }
        color_dict = {
            'red': 'красный',
            'orange': 'оранжевый',
            'yellow': 'желтый',
            'green': 'зеленый',
            'blue': 'синий',
            'white': 'белый',
            'black': 'черный',
        }
        if category:
            category = CategoryHandler.get_categories(slug=category)
            object_list = object_list.filter(category=category.id)
            sort_message = f'по категории - {category}'
        if tag:
            tag = TagHandler.get_tag(slug=tag)
            object_list = object_list.filter(tag=tag.id)
            sort_message = f'по тегу - {tag}'
        if request.GET.get('q'):
            q = request.GET.get('q')
            object_list = ItemHandler.search_item(q)
        if request.GET.get('title', None):
            title = request.GET.get('title')[:-1].title()
            object_list = Item.available_items.filter(title__icontains=title)
            all_colors_set = object_list
        if request.GET.get('price', None):
            price_min = int(request.GET.get('price').split(';')[0])
            price_max = int(request.GET.get('price').split(';')[1])
            object_list = object_list.filter(price__range=(price_min, price_max))
        if request.GET.getlist('color', None):
            color = request.GET.getlist('color')
            object_list = object_list.exclude(color=None).filter(color__in=color)
            color = {f'{c}': f'{color_dict[c]}' for c in color}
        if request.GET.get('order_by', None):
            order_by = request.GET.get('order_by')
            object_list = ItemHandler.ordering_items(queryset=object_list, order_by=order_by)
            sort_message = ItemHandler.ordering_message(order_by=order_by)
        get_param_dict = {}
        query_string_dict = parse_qs(request.META['QUERY_STRING'])
        for key, val in query_string_dict.items():
            if key in filter_dict.keys() and val:
                if key == 'price':
                    price_min = val[0].split(';')[0]
                    price_max = val[0].split(';')[1]
                    get_param_dict[f'от ${price_min} до ${price_max}'] = key
                elif key == 'color':
                    set_color = request.GET.getlist('color')
                    list_color = []
                    for index, color in enumerate(set_color):
                        list_color.append(color_dict[color])
                        get_param_dict[color_dict[color]] = val[index]
                elif key == 'order_by':
                    get_param_dict[sort_dict[val[0]]] = key
                else:
                    get_param_dict[val[0]] = key
        price_min_in_category = ItemHandler.get_range_price(all_colors_set).get('price__min')
        price_max_in_category = ItemHandler.get_range_price(all_colors_set).get('price__max')

        in_cart = get_items_in_cart(self.request)

        colors = get_colors(all_colors_set)
        tags = TagHandler.get_tags_queryset(object_list)
        queryset = self.my_paginator(object_list, self.request, self.paginate_by)
        if object_list:
            range_price = ItemHandler.get_range_price(object_list)
        else:
            range_price = ItemHandler.get_range_price(all_colors_set)
        context = {
            'in_cart': in_cart,
            'q': q,
            'category': category,
            'tag': tag,
            'set_tags': tags,
            'color': color,
            'set_colors': colors,
            'object_list': queryset,
            'range_price': range_price,
            'data_from_price__min': int(range_price.get('price__min', 0)),
            'data_from_price__max': int(range_price.get('price__max', 0)),
            'price_min_in_category': int(price_min_in_category),
            'price_max_in_category': int(price_max_in_category),
            'price_min': price_min,
            'price_max': price_max,
            'order_by': order_by,
            'sort_message': sort_message,
            'get_params': get_param_dict
        }
        return render(request, 'app_item/item_list.html', context=context)


class ItemBestSellerList(ItemList):
    """Класс-представление для отображения списка всех товаров отсортированных по продажам."""
    model = Item
    template_name = 'app_item/item_list.html'
    queryset = ItemHandler.get_bestseller()
    paginate_by = 6


class ItemNewList(ItemList):
    """Класс-представление для отображения списка всех новых товаров."""
    model = Item
    template_name = 'app_item/item_list.html'
    queryset = ItemHandler.get_new_item_list()
    paginate_by = 6


class FilterListView(ListView, MixinPaginator):
    """Класс-представление для отображения отфильтрованных товаров."""
    model = Item
    paginate_by = 8
    queryset = Item.available_items.all()

    def get_queryset(self, **kwargs):
        super().get_queryset()
        queryset = self.queryset

        if self.request.GET.get('price', None):
            price = self.request.GET.get('price').split(';')
            price_min = int(price[0])
            price_max = int(price[1])
            queryset = queryset.filter(price__range=(price_min, price_max))

        if self.request.GET.getlist('color', None):
            color = self.request.GET.getlist('color')
            queryset = queryset.exclude(color=None).filter(color__in=color)

        if self.request.GET.get('order_by', None):
            order_by = self.request.GET.get('order_by')
            queryset = ItemHandler.ordering_items(queryset=queryset, order_by=order_by)

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.get_queryset()
        queryset = self.my_paginator(items, self.request, self.paginate_by)
        context['object_list'] = queryset
        if self.request.GET.getlist('color', None):
            context['colors'] = self.request.GET.getlist('color', None)
        else:
            context['colors'] = get_colors(items)
        context['range_price'] = ItemHandler.get_range_price(queryset.object_list)
        context['sort_message'] = items.count()
        return context


class CategoryListView(ListView, MixinPaginator):
    """Класс-представление для отображения списка всех товаров по категориям."""
    model = Item
    paginate_by = 8
    queryset = Item.available_items.all()

    def get(self, request, *args, **kwargs):
        category = CategoryHandler.get_categories(slug=kwargs['category'])
        queryset = self.queryset.filter(category=category.id)
        self.queryset = queryset
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        super().get_queryset()
        queryset = self.queryset
        if self.request.GET.get('price', None):
            price = self.request.GET.get('price').split(';')
            price_min = int(price[0])
            price_max = int(price[1])
            queryset = queryset.filter(price__range=(price_min, price_max))

        if self.request.GET.getlist('color', None):
            color = self.request.GET.getlist('color')
            queryset = queryset.exclude(color=None).filter(color__in=color)

        if self.request.GET.get('order_by', None):
            order_by = self.request.GET.get('order_by')
            queryset = ItemHandler.ordering_items(queryset=queryset, order_by=order_by)

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.get_queryset()
        queryset = self.my_paginator(items, self.request, self.paginate_by)
        context['object_list'] = queryset
        if self.request.GET.getlist('color', None):
            context['colors'] = self.request.GET.getlist('color', None)
        else:
            context['colors'] = get_colors(items)
        context['range_price'] = ItemHandler.get_range_price(items)
        context['sort_message'] = items.count()
        return context


class ItemDetail(DetailView, CreateView):
    """Класс-представление для отображения одного товара."""
    model = Item
    context_object_name = 'item'
    template_name = 'app_item/item_detail.html'
    form_class = CommentForm
    success_url = '/'

    def get(self, request, *args, **kwargs):
        """
        Get-функция для отображения одного товара.
        Добавляет товар к списку просмотренных товаров пользователя
        и добавляет IP-адрес пользователя к товару.
        """
        item = self.get_object()
        user = request.user
        form = self.get_form()

        # создание записи в БД о просмотренном товаре пользователем
        try:
            AddItemToReview().add_item_to_review(user=user, item_id=item.id)
        except ObjectDoesNotExist:
            pass

        # увеличивает количество просмотров товара
        CountView().add_view(request, item_id=item.id)

        # список всех тегов товара
        tags = TagHandler.get_tags_queryset(item_id=item.id)

        # общее кол-во комментариев к товару
        comments_count = CommentHandler.get_comment_cont(item.id)

        context = {
            'form': form,
            'tags': tags,
            'item': item,
            'comments_count': comments_count,
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
        return redirect(self.request.get_full_path())

    def get_success_url(self):
        return reverse('app_item:item_detail', args=[self.request.pk])


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
            comment.save(force_update=True)
            return redirect('app_item:item_detail', item_id)
        return render(request, self.template_name, {'form': form, 'comments': comment})


def remove_param(request, param):
    """Функция для удаления параметров фильтра в строке-запроса."""

    query_string = request.META.get('HTTP_REFERER').split('?')
    query_string_dict = parse_qs(query_string[1])
    if param in query_string_dict.keys():
        query_string_dict.pop(param, None)
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
