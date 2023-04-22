from typing import List, Dict, Union, Any
from functools import reduce
from operator import and_
import random
from urllib.parse import parse_qs
from datetime import date, timedelta
from django.core.cache import cache
from django.core.checks import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models import Min, Max, Q, Count
from django.http import Http404

from app_item.models import Item, Category, Tag, IpAddress, FeatureValue, Comment
from utils.my_utils import query_counter


def get_colors(queryset: QuerySet) -> List[str]:
    """
    Функция возвращает все цвета, которые есть у выбранных товаров/
    :param queryset: queryset товаров,
    :return: список цветов всех выбранных товаров
    """
    try:
        colors = queryset.exclude(color=None).values('color').distinct()
        colors = list(colors.values('color'))
        colors_list = []
        for color in colors:
            for key, val in color.items():
                colors_list.append(val)
        colors = list(set(colors_list))
        return colors
    except:
        return []


class ItemHandler:
    COLOR_DICT = {

    }

    @staticmethod
    def get_item(item_id: int) -> Any:
        """Функция возвращает экземпляр класса Item.
        :param item_id:  id-товара
        :return: экземпляр товара или None
        """
        try:
            return Item.objects.select_related('category').get(id=item_id)
        except ObjectDoesNotExist:
            raise Http404('Не найден ни один товар, соответствующий запросу')

    @staticmethod
    def min_and_max_price(min_price: int, max_price: int) -> QuerySet:
        """Функция возвращает отсортированный queryset товаров в заданном диапозоне цен.
         :param min_price:  минимальная цена
         :param max_price:  максимальная цена
         :return: отсортированный queryset товара.
         """
        items = Item.objects.filter(price__range=(min_price, max_price))
        return items

    @staticmethod
    @query_counter
    def get_range_price(queryset: QuerySet) -> (tuple, int):
        """ Функция возвращает кортеж из максимальной и минимальной цен переданного queryset. """
        if not queryset:
            return {'price__min': None, 'price__max': None}
        return queryset.aggregate(Min('price'), Max('price')).values()

    @staticmethod
    def get_popular_items(items=None) -> QuerySet:
        """Функция возвращает список экземпляров популярных товаров"""
        if not items:
            popular_items = Item.objects.annotate(view=Count('views')).order_by('-view')
            return popular_items
        popular = items.exclude(item_views=None).annotate(view=Count('views')).order_by('-view')
        cache.get_or_set('popular', popular, 60)
        return popular

    @staticmethod
    def get_comments_items(items=None) -> QuerySet:
        """Функция возвращает список экземпляров самых комментируемых товаров"""
        if not items:
            return Item.objects.none()
        return items.annotate(comm=Count('item_comments')).order_by('-comm')

    @staticmethod
    def get_limited_edition_items() -> QuerySet:
        """Функция возвращает список экземпляров товаров «Ограниченный тираж»."""
        limited_items = Item.available_items.prefetch_related('tag').filter(limited_edition=True)
        cache.get_or_set('limited_items', limited_items, 60)
        return limited_items

    @staticmethod
    def get_bestseller(queryset=None) -> QuerySet:
        """Функция возвращает список экземпляров товаров «Лучшие по продажам».
            :param queryset: queryset товаров
            :return: отсортированный queryset товара.
        """
        if not queryset:
            queryset = Item.available_items.annotate(bestseller=Count('cart_item__quantity')).order_by('-bestseller')
        else:
            queryset = queryset.annotate(bestseller=Count('cart_item__quantity')).order_by('-bestseller')
        return queryset

    @staticmethod
    def get_new_item_list() -> QuerySet:
        """Функция возвращает список экземпляров товаров новинки."""

        today = date.today()
        last_four_week = today - timedelta(days=30)
        new_items = Item.available_items. \
            select_related('category'). \
            prefetch_related('tag', 'views', 'image'). \
            filter(created__gt=last_four_week). \
            order_by('-created')
        return new_items

    @staticmethod
    def get_history_views(user):
        return Item.objects.filter(views__user=user).annotate(items_for_you=Count('item_views')).order_by('created')

    @staticmethod
    def get_items_for_you(request=None) -> list:
        """
        Функция возвращает список queryset товаров,
        на основе ранее посещаемых товаров.

        На основе queryset товаров определяется 5 самых популярных категорий,
        затем в случайном порядке выбирается 12 товаров по три из каждой категории.
        :param request: request
        :return: отсортированный список товаров.
        """
        if not request.user.is_authenticated:
            view_items = Item.available_items.prefetch_related('view').annotate(
                items_for_you=Count('item_views')).order_by('-created')[:24]
        else:
            user = request.user
            view_items = Item.available_items.prefetch_related('view').filter(views__user=user).annotate(
                items_for_you=Count('item_views')).order_by('-created')[:5]
            if not view_items.exists():
                view_items = Item.available_items.prefetch_related('view'). \
                                 annotate(items_for_you=Count('item_views')).order_by('-created')[:24]
        related_categories = Category.objects.select_related('items').values_list('id', flat=True). \
                                 filter(items__in=view_items).distinct()[:5]
        query_list = []
        for category in related_categories:
            item_set = Item.available_items.select_related('category').prefetch_related('cart_item'). \
                           filter(category=category).order_by('cart_item__quantity')[:2]
            query_list.extend(item_set)
        random_list = random.sample(range(len(query_list)), len(query_list))
        queryset = [query_list[i] for i in random_list]

        return queryset

    @staticmethod
    def search_item(query) -> QuerySet:
        query = str(query).title()
        items = Item.objects.filter(
            Q(category__title__icontains=query) |
            Q(title__icontains=query) |
            Q(tag__title__icontains=query)
        ).distinct()

        return items

    @staticmethod
    def ordering_items(queryset: QuerySet, order_by: str) -> QuerySet:
        if order_by == 'cheep_first':
            queryset = queryset.order_by('price')
        elif order_by == 'rich_first':
            queryset = queryset.order_by('-price')
        elif order_by == '-created':
            queryset = queryset.order_by('-created')
        elif order_by == 'best_seller':
            queryset = ItemHandler.get_bestseller(queryset)
        elif order_by == 'by_comments':
            queryset = ItemHandler.get_comments_items(queryset)
        elif order_by == 'by_reviews':
            queryset = ItemHandler.get_popular_items(queryset)

        return queryset

    @staticmethod
    def ordering_message(sort_param: str) -> str:

        message_book = {
            'best_seller': 'по продажам',
            '-best_seller': 'по продажам',
            'by_comments': 'по количеству комментариев',
            'by_reviews': 'по количеству просмотров',
            'cheep_first': 'по увеличению цены',
            'rich_first': 'по уменьшении цены',
            '-created': 'по новизне',
        }
        return message_book[sort_param] if sort_param else None

    @staticmethod
    def filter_queryset_by_request_param(queryset: QuerySet, param, value) -> QuerySet:

        request_book = {
            'is_available': ItemHandler.get_available(queryset=queryset),
            'store': queryset.filter(store__slug=value[0]),
            'q': Item.objects.filter(Q(category__title__icontains=value) |
                                     Q(title__icontains=value) |
                                     Q(tag__title__icontains=value)
                                     ).distinct(),
            'title': Item.objects.filter(Q(category__title__icontains=value) |
                                         Q(title__icontains=value) |
                                         Q(tag__title__icontains=value)
                                         ).distinct(),
            'color': queryset.exclude(color=None).filter(color__in=value),
            'order_by': ItemHandler.ordering_items(queryset, order_by=value[0]),
            'price': ItemHandler.filter_queryset_by_price(queryset, price=value)
        }
        if param in request_book.keys():
            return request_book[param]

    @staticmethod
    def filter_queryset_by_store(queryset: QuerySet, store) -> QuerySet:
        """Функция возвращает отфильтрованный queryset товаров по одному магазину.
            :param queryset: queryset товаров
            :param store: магазин
            :return: отсортированный queryset товара.
        """
        try:
            # items = queryset.filter(store=store)
            items = queryset.filter(store__slug=store)
        except ObjectDoesNotExist:
            items = queryset

        return items

    @staticmethod
    def filter_queryset_by_price(queryset: QuerySet, price) -> QuerySet:
        """Функция возвращает отфильтрованный queryset товаров по диапазону цен.
            :param queryset: queryset товаров
            :param price: диапазон цен
            :return: отсортированный queryset товара.
        """
        try:
            price_min = int(price.split(';')[0])
            price_max = int(price.split(';')[1])
            items = queryset.filter(price__range=(price_min, price_max))
        except ObjectDoesNotExist:
            items = queryset

        return items

    @staticmethod
    def get_available(queryset):
        queryset = queryset.filter(is_available=True)
        return queryset

    @staticmethod
    def make_get_param_dict(request):
        # query_string_dict = dict(self.request.GET)  # словарь всех параметров GET запроса
        # создает словарь из всех параметров GET-запроса.
        # ключ записывает человеко-читаемое название параметра, в значение имя ключа из GET-запросов
        # для корректного отображения всех выбранных параметров в фильтре на странице сайта
        filter_dict = {
            'order_by': 'отсортировано',
            'price': 'цена',
            'color': 'цвет',
            'title': 'название',
            'page': 'страница',
            'q': 'запрос',
            'is_available': 'в наличии',
            'store': 'магазин',
            'cheep_first': 'сначала дороже',
            'rich_first': 'сначала дешевле',
            'best_seller': 'лидеры продаж',
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
            'brown': 'коричневый'
        }
        query_string_dict = parse_qs(request.META.get('QUERY_STRING'))
        get_param_dict = {}
        feature_list = []

        for key, value in query_string_dict.items():
            if key not in filter_dict.keys() and value:
                # поиск по дополнительным характеристикам
                if len(value) > 1:
                    feature = FeatureValue.objects.prefetch_related('item_features').filter(slug__in=value)
                    for feature_key in feature:
                        get_param_dict[f'{feature_key.feature.title} - {feature_key.value}'] = feature_key.slug
                else:
                    feature = FeatureValue.objects.prefetch_related('item_features').get(slug=value[0])
                    get_param_dict[f'{feature.feature.title} - {feature.value}'] = feature.slug
                feature_list.append(feature)
            else:
                # поиск по цене
                if key == 'price':
                    price_min, price_max = value[0].split(';')
                    get_param_dict[f'от ${price_min} до ${price_max}'] = key
                # поиск по цвету
                elif key == 'color':
                    set_color = request.GET.getlist('color')
                    list_color = []
                    for index, color in enumerate(set_color):
                        list_color.append(color_dict[color])
                        get_param_dict[color_dict[color]] = value[index]
                elif key == 'order_by':
                    # сортировка
                    get_param_dict[filter_dict[value[0]]] = key
                elif key == 'is_available':
                    # фильтр товаров по их наличию и доступности на сайте
                    get_param_dict['в наличии'] = key
                elif key == 'page':
                    pass
                # поиск по названию
                elif key in ('q', 'title') and len(value[0]) > 1:
                    get_param_dict[f'по запросу -"{value[0]}"'] = key
                elif key == 'store':
                    get_param_dict[f'магазин - {value[0]}'] = key
                else:
                    get_param_dict[value[0]] = key
        return get_param_dict

    @staticmethod
    def smart_filter(request, object_list, query_get_param_dict: dict):

        # фильтрует базу товаров по нескольким параметрам запроса объединенных в группы
        # каждый результат фильтрации добавляется в список
        # итоговый список через лист-comprehension объединяется в один запрос по средство "Q() &"

        filter_dict = {
            'order_by': 'сортировка',
            'price': 'цена',
            'color': 'цвет',
            'title': 'название',
            'page': 'страница',
            'q': 'запрос',
            'is_available': 'в наличии',
            'store': 'магазин',
        }
        query_get_param_dict = parse_qs(request.META.get('QUERY_STRING'))
        all_queryset_list = []
        object_list = object_list.select_related('category', 'store'). \
            prefetch_related('tag', 'views', 'image', 'feature_value')

        for param, value in query_get_param_dict.items():
            if param in filter_dict.keys():
                if param == 'title':
                    title = request.GET.get('title')
                    queryset = object_list.filter(title__icontains=title)
                    all_queryset_list.append(queryset)
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == 'color':
                    color = query_get_param_dict.get('color')
                    queryset = object_list.filter(color__in=color)
                    all_queryset_list.append(queryset)
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == 'price':
                    price_range = request.GET.get('price', None)
                    queryset = ItemHandler.filter_queryset_by_price(object_list, price=price_range)
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == 'q':
                    query = str(request.GET.get('q'))  # [:-1]
                    title = query.title()
                    lower = query.lower()
                    queryset = object_list.select_related('category', 'store'). \
                        prefetch_related('tag', 'views', 'image', 'feature_value'). \
                        filter(
                        Q(category__title__icontains=title) |
                        Q(title__icontains=title) |
                        Q(tag__title__icontains=title) |
                        Q(category__title__icontains=lower) |
                        Q(title__icontains=lower) |
                        Q(tag__title__icontains=lower) |
                        Q(store__title__icontains=lower)
                    ).distinct()
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == 'is_available':
                    queryset = object_list.filter(is_available=True)
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == 'order_by':
                    pass
            else:
                # поиск по спецификация конкретной категории товаров
                feature_value_list = query_get_param_dict[param]
                values_list = FeatureValue.objects.filter(slug__in=feature_value_list).values_list('id', flat=True)
                for v in values_list:
                    queryset = object_list.filter(feature_value=v)
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)

        if len(all_queryset_list) > 0:
            object_list = reduce(and_, [i for i in all_queryset_list])

        return object_list


class TagHandler:
    @staticmethod
    def get_tags_queryset(queryset=None, item_id: Union[int, None] = None) -> QuerySet[Tag]:
        """
        Функция возвращает queryset-тегов.
        При наличии параметра отфильтрованный queryset-тегов.
        :param item_id: id-товара
        :param queryset: queryset-товаров
        :return: queryset-тегов
        """
        try:
            if queryset:
                tags = Tag.objects.prefetch_related('item_tags'). \
                    filter(item_tags__in=queryset). \
                    annotate(item_count=Count('item_tags')). \
                    order_by('-item_count')
            elif item_id:
                tags = Tag.objects.prefetch_related('item_tags').filter(item_tags=item_id)
            else:
                tags = Tag.objects.all()
            return tags
        except ObjectDoesNotExist:
            raise Http404

    @staticmethod
    def get_tag(slug: str):
        """
           Функция возвращает один экземпляр тега.
           :param slug: slug-тега товара
           :return: если есть параметр возвращает
                    экземпляр тега или Http404.
           """
        try:
            tag = Tag.objects.prefetch_related('item_tags').get(slug=slug)
            return tag
        except ObjectDoesNotExist:
            raise Http404('такого тега не существует')

    @staticmethod
    def filter_queryset_by_tag(queryset: QuerySet, tag) -> QuerySet:
        """
            Функция возвращает queryset-товаров отфильтрованный по тегу.
            :param queryset: queryset товаров
            :param tag: тег по которому нужно отфильтровать
            :return: queryset.
        """
        tag = TagHandler.get_tag(slug=tag)
        queryset = queryset.select_related('category', 'store'). \
            prefetch_related('tag', 'views', 'image', 'feature_value'). \
            filter(tag=tag.id)

        return queryset

    @staticmethod
    def get_abc_ordered() -> dict:
        """Функция возвращает словарь с отсортированными тегами по алфавиту."""
        tags = Tag.objects.all()
        tag_book = dict()
        abc = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        for key in abc:
            tag_book[key] = list()

        for key, value in tag_book.items():
            for tag in tags:
                t = tag.title[:1]
                if t == key:
                    if tag not in value:
                        value.append(tag)
                        tag_book[key] = value
        return tag_book


class CategoryHandler:
    @staticmethod
    def get_categories(slug=None):
        """
        Функция возвращает queryset-категорий товаров.
        При наличии параметра отфильтрованный queryset-категорий.
        :param slug: slug-товара
        :return: queryset-категорий.
        """
        try:
            if slug:
                category = Category.objects.select_related('parent_category').get(slug=slug)
            else:
                category = Category.objects.select_related('parent_category').exclude(items=None)
            return category
        except ObjectDoesNotExist:
            raise Http404('Не найдена ни одина категория товаров, соответствующий запросу')

    @staticmethod
    def get_related_category_list(queryset: QuerySet) -> QuerySet:
        """
          Функция возвращает queryset всех категорий,
           которые относятся к выбранным товарам .
          :return: queryset-категорий.

          """

        related_categories = Category.objects. \
            values_list('parent_category__sub_categories', flat=True). \
            filter(items__in=queryset). \
            distinct()
        related_categories = Category.objects.filter(id__in=related_categories)
        category = Category.objects.filter(items__in=queryset).distinct()

        return related_categories if related_categories.exists() else category

    @staticmethod
    def get_related_items(queryset: QuerySet) -> QuerySet:
        return Category.objects.select_related('items').filter(items__in=queryset).values_list('id',
                                                                                               flat=True).distinct()

    @staticmethod
    def get_categories_by_id(category_id=None):
        """
        Функция возвращает queryset-категорий товаров.
        При наличии параметра отфильтрованный queryset-категорий.
        :param category_id: id-товара
        :return: queryset-категорий.
        """
        if category_id:
            category = Category.objects.select_related('parent_category').get(id=category_id)
        else:
            category = Category.objects.select_related('parent_category').all()
        return category

    @staticmethod
    def get_categories_in_items_set(items):
        """Функция возвращает queryset-категорий  определенных товаров.

        :param items: queryset-товаров
        :return:queryset-категорий.
        """
        items_id_tuple = set(items.values_list('category'))
        items_list = [item[0] for item in items_id_tuple]
        categories = Category.objects.select_related('parent_category').filter(id__in=items_list)
        return categories

    @staticmethod
    def filter_items_by_category(queryset: QuerySet, category) -> QuerySet:
        category = CategoryHandler.get_categories(slug=category)
        queryset = queryset.select_related('category', 'store'). \
            prefetch_related('tag', 'views', 'image', 'feature_value'). \
            filter(Q(category=category.id) | Q(category__parent_category=category.id))
        return queryset


class CountView:

    def get_client_ip(self, request):
        """Функция для получения IP-адреса пользователя."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def add_view(self, request, item_id):
        """Функция для добавления просмотров товара."""
        item = ItemHandler().get_item(item_id)
        if request.user.is_authenticated:
            user = request.user
            ip_address, created = IpAddress.objects.get_or_create(user=user)
        else:
            ip = self.get_client_ip(request)
            ip_address, created = IpAddress.objects.get_or_create(ip=ip)
        if ip_address not in item.views.all():
            item.views.add(ip_address)


class RelatedObjectDoesNotExist(ObjectDoesNotExist):
    pass


class AddItemToReview:
    """
    Класс для добавления товара в список просматриваемых пользователем.
    Определяет три самых популярный категории товаров у пользователя.
    """

    @staticmethod
    def _get_reviews_items(user):
        """Функция возвращает все товары, которые просматривал пользователь."""
        if user.is_authenticated:
            return user.profile.review_items.select_related('category').all()
        return ItemHandler.get_popular_items()

    @staticmethod
    def _get_favorite_category_list(all_reviewed_item) -> List[int]:
        """Функция возвращает список самых просматриваемых ID-категорий товаров."""
        favorite_category = all_reviewed_item.values_list('category').annotate(rating=Count('category')). \
            order_by('-rating')
        favorite_category_list = [category_id[0] for category_id in favorite_category if category_id[0]]
        return favorite_category_list

    @staticmethod
    def _get_min_price(category_id: int) -> float:
        """Функция возвращает самую низкую цену на товар в категории."""
        category = CategoryHandler.get_categories_by_id(category_id)
        min_price = category.items.values_list('price', flat=True).aggregate(min_price=Min('price'))
        return float(min_price.get('min_price'))

    @staticmethod
    def _get_favorite_category_and_price_dict(favorite_category_list: List[int],
                                              category_list: QuerySet[Category]) -> List[Dict[str, Union[str, float]]]:
        """Функция возвращает список из словарей(категория, цена)."""

        favorite_category = []
        for category_id in favorite_category_list:
            favorite_category.append(
                {
                    'category': category_list.get(id=category_id),
                    'price': AddItemToReview._get_min_price(category_id=category_id)
                }
            )
        return favorite_category[:3]

    @staticmethod
    def get_best_price_in_category(user):
        """Функция возвращает самые популярные категории товаров у пользователя."""

        all_reviewed_item = AddItemToReview._get_reviews_items(user)
        cache.get_or_set('all_reviewed_item', all_reviewed_item, 60)
        all_category_list = CategoryHandler.get_categories()

        favorite_category_list = AddItemToReview._get_favorite_category_list(all_reviewed_item)
        cache.get_or_set('favorite_category_list', favorite_category_list, 60)
        favorite_category_best_price = AddItemToReview._get_favorite_category_and_price_dict(
            favorite_category_list,
            all_category_list
        )
        cache.get_or_set('favorite_category_best_price', favorite_category_best_price, 60)
        return favorite_category_best_price

    @staticmethod
    def add_item_to_review(user, item_id):
        """
        Функция добавляет товар в список просмотренных,
        обновляет список избранных категорий пользователя.
        :param user: пользователь
        :param item_id: id-товара
        :return:
        """
        item = ItemHandler.get_item(item_id)
        reviews = AddItemToReview._get_reviews_items(user)
        if item not in reviews:
            try:
                user.profile.review_items.add(item)
            except RelatedObjectDoesNotExist:
                pass
        AddItemToReview.get_best_price_in_category(user)
        return reviews
