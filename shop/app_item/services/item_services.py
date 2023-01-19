from typing import List, Dict, Union, Any

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models import Count, Min, Max, Q
from app_item.models import Item, Category, Tag, IpAddress


def get_colors(queryset: QuerySet) -> List[str]:
    """
    Функция возвращает все цвета, которые есть у выбранных товаров/
    :param queryset: queryset товаров,
    :return: список цветов всех выбранных товаров
    """

    colors = queryset.exclude(color=None).values('color').distinct()
    colors = list(colors.values('color'))
    colors_list = []
    for color in colors:
        for key, val in color.items():
            colors_list.append(val)
    colors = list(set(colors_list))
    return colors


class ItemHandler:
    @staticmethod
    def get_item(item_id: int) -> Any:
        """Функция возвращает экземпляр класса Item.
        :param item_id:  id-товара
        :return: экземпляр товара или None
        """
        try:
            return Item.objects.select_related('category').get(id=item_id)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def min_and_max_price(min_price, max_price):
        items = Item.objects.filter(price__range=(min_price, max_price))
        return items

    @staticmethod
    def get_range_price(queryset):
        try:
            range_price = queryset.aggregate(Min('price'), Max('price'))
            return range_price
        except ObjectDoesNotExist:
            return 0

    @staticmethod
    def get_popular_items(items=None):
        """Функция возвращает список экземпляров популярных товаров"""
        if not items:
            popular_items = Item.available_items.annotate(view=Count('views')).order_by('-view')
            cache.get_or_set('popular_items', popular_items, 60)
            return popular_items
        popular = items.exclude(item_views=None).annotate(view=Count('views')).order_by('-view')
        cache.get_or_set('popular', popular, 60)
        return popular

    @staticmethod
    def get_comments_items(items=None):
        """Функция возвращает список экземпляров самых комментируемых товаров"""
        if not items:
            return Item.available_items.annotate(comm=Count('item_comments')).order_by('-comm')
        return items.exclude(item_comments=None).annotate(comm=Count('item_comments')).order_by('-comm')

    @staticmethod
    def get_limited_edition_items():
        """Функция возвращает список экземпляров товаров «Ограниченный тираж»."""
        limited_items = Item.available_items.prefetch_related('tag').filter(limited_edition=True)
        cache.get_or_set('limited_items', limited_items, 60)
        return limited_items

    @staticmethod
    def get_bestseller(items=None, desc=False):
        """Функция возвращает список экземпляров товаров «Лучшие по продажам»."""
        if not items:
            return Item.available_items.prefetch_related('tag').annotate(bestseller=Count('cart_item')).order_by(
                '-bestseller')
        if desc:
            return items.exclude(cart_item=None).filter(cart_item__is_paid=True).annotate(
                bestseller=Count('cart_item')).order_by('bestseller')
        return items.exclude(cart_item=None).filter(cart_item__is_paid=True).annotate(
            bestseller=Count('cart_item')).order_by('-bestseller')

    @staticmethod
    def get_new_item_list():
        """Функция возвращает список экземпляров товаров новинки."""
        new_items = Item.available_items.\
            select_related('category').\
            prefetch_related('tag', 'views', 'image').\
            order_by('-created')
        cache.get_or_set('new_items', new_items, 60)
        return new_items

    @staticmethod
    def search_item(query):
        items = Item.available_items.filter(
            Q(category__title__icontains=query) |
            Q(title__icontains=query) |
            Q(tag__title__icontains=query)
        )
        return items

    @staticmethod
    def ordering_items(queryset, order_by):
        sort_book = {
            '-price': queryset.order_by('-price'),
            'price': queryset.order_by('price'),
            '-created': queryset.order_by('-created'),
            'best_seller': ItemHandler.get_bestseller(queryset),
            '-best_seller': ItemHandler.get_bestseller(queryset, desc=True),
            'by_comments': ItemHandler.get_comments_items(queryset),
            'by_reviews': ItemHandler.get_popular_items(queryset),

        }
        return sort_book[order_by]

    @staticmethod
    def ordering_message(order_by):
        message_book = {
            'best_seller': 'по продажам',
            '-best_seller': 'по продажам',
            'by_comments': 'по количеству комментариев',
            'by_reviews': 'по количеству просмотров',
            '-price': 'по уменьшении цены',
            'price': 'по увеличению цены',
            '-created': 'по новизне',
        }
        return message_book[order_by]


class TagHandler:
    @staticmethod
    def get_tags_queryset(queryset=None, item_id: Union[int, None] = None) -> QuerySet[Tag]:
        """
        Функция возвращает queryset-тегов.
        При наличии параметра отфильтрованный queryset-тегов.
        :param item_id: id-товара
        :param queryset: queryset-товаров
        :return: queryset-тегов.
        """

        if queryset:
            tags = Tag.objects.filter(item_tags__in=queryset).annotate(item_count=Count('item_tags')).order_by(
                '-item_count')
        elif item_id:
            tags = Tag.objects.filter(item_tags=item_id)
        else:
            tags = Tag.objects.all()
        return tags

    @staticmethod
    def get_tag(slug: str):
        """
           Функция возвращает один экземпляр тега.
           :param slug: slug-тега товара
           :return: если есть параметр возвращает
                    экземпляр тега  или None.
           """
        try:
            return Tag.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return None

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
        if slug:
            category = Category.objects.select_related('parent_category').get(slug=slug)
        else:
            category = Category.objects.select_related('parent_category').exclude(items=None)
        return category

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
        ip = self.get_client_ip(request)
        item = ItemHandler().get_item(item_id)
        if IpAddress.objects.filter(ip=ip).exists():
            item.views.add(IpAddress.objects.get(ip=ip))
        else:
            IpAddress.objects.create(ip=ip)
            item.views.add(IpAddress.objects.get(ip=ip))


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
        return favorite_category

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
