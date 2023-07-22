"""
Модуль содержит класс-сервис для работы с товарам.

1. ItemHandler - класс для работы с товарами,
2. TagHandler - класс для работы с тегами,
3. CategoryHandler - класс для работы с категориями,
4. CountView - класс для работы с количеством просмотров страницы товара,
5. AddItemToReview - класс для добавления товара в список просматриваемых,
6. ImageHandler - класс для работы с изображениями,
7. QueryStringHandler - класс для работы со строкой GET-запроса,
8. FeatureHandler - класс для работы с характеристиками товара,
9. ValueHandler - класс для работы со значениями характеристик товара.
10. get-color - функция для работы с цветами товара.
"""

import random
from io import BytesIO
from PIL import Image as PilImage
from django.core.files.uploadedfile import InMemoryUploadedFile
from typing import List, Dict, Union
from functools import reduce
from operator import or_
from datetime import date, timedelta
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.query import QuerySet
from django.db.models import Min, Max, Q, Count, F, Model
from django.http import Http404, HttpRequest
from urllib.parse import urlencode
from urllib.parse import parse_qs

from django.shortcuts import get_object_or_404

from app_item import models as item_models
from app_item import forms as item_forms
from app_item.services import comment_services
from utils.my_utils import MixinPaginator


class ItemHandler:
    """Класс для работы с товарами."""

    @staticmethod
    def get_all_items():
        """Функция возвращет все товары и БД."""
        return item_models.Item.objects.all()

    @staticmethod
    def get_item(item_id: int) -> QuerySet:
        """Функция возвращает экземпляр класса Item.

        :param item_id:  id-товара
        :return: экземпляр товара или None
        """
        try:
            return item_models.Item.objects.select_related("category").get(
                id=item_id
            )
        except ObjectDoesNotExist:
            raise Http404("Не найден ни один товар, соответствующий запросу")

    @staticmethod
    def min_and_max_price(min_price: int, max_price: int) -> QuerySet:
        """
        Функция возвращает отсортированный queryset товаров
        в заданном диапозоне цен.

        :param min_price:  минимальная цена
        :param max_price:  максимальная цена
        :return: отсортированный queryset товара.
        """
        items = item_models.Item.objects.filter(
            price__range=(min_price, max_price)
        )
        return items

    @staticmethod
    def get_range_price(queryset: QuerySet) -> (tuple, int):
        """
        Функция возвращает кортеж.

        Возвращает кортеж из максимальной и минимальной цен
        переданного queryset.
        """
        if not queryset:
            return None, None
        return queryset.aggregate(Min("price"), Max("price")).values()

    @staticmethod
    def get_popular_items(items=None) -> QuerySet[item_models.Item]:
        """Функция возвращает список экземпляров популярных товаров."""
        if items:
            popular_items = (
                items.exclude(item_views=None)
                .annotate(view=Count("views"))
                .order_by("-view")
            )
        else:
            popular_items = item_models.Item.objects.annotate(
                view=Count("views")
            ).order_by("-view")

        return popular_items

    @staticmethod
    def get_comments_items(items=None) -> QuerySet[item_models.Item]:
        """Функция возвращает список самых комментируемых товаров."""
        if not items:
            return item_models.Item.objects.none()
        return items.annotate(comm=Count("item_comments")).order_by("-comm")

    @staticmethod
    def get_limited_edition_items() -> QuerySet[item_models.Item]:
        """Функция возвращает список товаров «Ограниченный тираж»."""
        limited_items = item_models.Item.available_items.prefetch_related(
            "tag"
        ).filter(limited_edition=True)

        return limited_items

    @staticmethod
    def get_bestseller(queryset=None) -> QuerySet[item_models.Item]:
        """
        Функция возвращает queryset товаров «Лучшие по продажам».

        :param queryset: queryset товаров
        :return: отсортированный queryset товара.
        """
        base = item_models.Item.objects.annotate(
            quantity=F("cart_item__order_item__quantity")
        )
        queryset = queryset if queryset else base
        queryset = (
            queryset.annotate(quantity=F("cart_item__order_item__quantity"))
            .filter(quantity__gt=0)
            .order_by("-quantity")
            .distinct()
        )

        return queryset

    @staticmethod
    def get_new_item_list() -> QuerySet[item_models.Item]:
        """Функция возвращает queryset товаров «Новинки»."""
        last_four_week = date.today() - timedelta(days=300)

        new_items = (
            item_models.Item.available_items.select_related("category")
            .prefetch_related("tag", "views", "images")
            .filter(created__gt=last_four_week)
            .order_by("-created")
        )

        return new_items

    @staticmethod
    def get_history_views(user) -> QuerySet[item_models.Item]:
        """Функция возвращает queryset просматриваемых товаров."""
        items = (
            item_models.Item.objects.filter(views__user=user)
            .annotate(items_for_you=Count("item_views"))
            .order_by("created")
        )

        return items

    @staticmethod
    def get_items_for_you(request, paginate_by: int) -> dict:
        """
        Функция возвращает словарь с queryset товаров,
        на основе ранее посещаемых товаров.

        На основе queryset товаров определяется 5 самых
        популярных категорий,
        затем в случайном порядке выбирается 12 товаров
        по 3 из каждой категории.
        :param paginate_by: кол-во товаров для пагинации
        :param request: HttpRequest
        :return: context-словарь.
        """
        if not request.user.is_authenticated:
            view_items = (
                item_models.Item.available_items.prefetch_related("view")
                .annotate(items_for_you=Count("item_views"))
                .order_by("-created")[:24]
            )
        else:
            user = request.user
            view_items = (
                item_models.Item.available_items.prefetch_related("view")
                .filter(views__user=user)
                .annotate(items_for_you=Count("item_views"))
                .order_by("-created")[:5]
            )

            if not view_items.exists():
                view_items = (
                    item_models.Item.available_items.prefetch_related("view")
                    .annotate(items_for_you=Count("item_views"))
                    .order_by("-created")[:24]
                )
        related_categories = (
            item_models.Category.objects.select_related("items")
            .values_list("id", flat=True)
            .filter(items__in=view_items)
            .distinct()[:5]
        )

        query_list = []
        for category in related_categories:
            item_set = (
                item_models.Item.available_items.select_related("category")
                .prefetch_related("cart_item")
                .filter(category=category)
                .order_by("cart_item__quantity")[:2]
            )
            query_list.extend(item_set)
        random_list = random.sample(range(len(query_list)), len(query_list))
        queryset = [query_list[i] for i in random_list]
        context = {
            "object_list": MixinPaginator(
                queryset, request, paginate_by
            ).my_paginator()
        }
        return context

    @staticmethod
    def ordering_items(
        queryset: QuerySet[item_models.Item], order_by: str
    ) -> QuerySet[item_models.Item]:
        """Функция возвращает отсортированный Queryset по переданному параметру."""
        if order_by == "cheep_first":
            queryset = queryset.order_by("price")
        elif order_by == "rich_first":
            queryset = queryset.order_by("-price")
        elif order_by == "-created":
            queryset = queryset.order_by("-created")
        elif order_by == "best_seller":
            queryset = ItemHandler.get_bestseller(queryset)
        elif order_by == "by_comments":
            queryset = ItemHandler.get_comments_items(queryset)
        elif order_by == "by_reviews":
            queryset = ItemHandler.get_popular_items(queryset)

        return queryset

    @staticmethod
    def ordering_message(sort_param: str) -> str:
        """Функция возвращает сообщение сортировки."""
        message_book = {
            "best_seller": "по продажам",
            "-best_seller": "по продажам",
            "by_comments": "по количеству комментариев",
            "by_reviews": "по количеству просмотров",
            "cheep_first": "по увеличению цены",
            "rich_first": "по уменьшении цены",
            "-created": "по новизне",
        }
        return message_book[sort_param] if sort_param else None

    @staticmethod
    def filter_queryset_by_request_param(
        queryset: QuerySet[item_models.Item], param: str, value: str
    ) -> QuerySet[item_models.Item]:
        """
        Функция возращает отфильтрованный queryset товаров.

        :param queryset: queryset-товаров
        :param param: параметр фильтрации или сортировки
        :param value: значение фильтрации или сортировки
        :return: отсортированный queryset товара.
        """
        request_book = {
            "is_available": ItemHandler.get_available(queryset=queryset),
            "store": queryset.filter(store__slug=value[0]),
            "q": item_models.Item.objects.filter(
                Q(category__title__icontains=value)
                | Q(title__icontains=value)
                | Q(tag__title__icontains=value)
            ).distinct(),
            "title": item_models.Item.objects.filter(
                Q(category__title__icontains=value)
                | Q(title__icontains=value)
                | Q(tag__title__icontains=value)
            ).distinct(),
            "color": queryset.exclude(color=None).filter(color__in=value),
            "order_by": ItemHandler.ordering_items(
                queryset, order_by=value[0]
            ),
            "price": ItemHandler.filter_queryset_by_price(
                queryset, price=value
            ),
        }
        if param in request_book.keys():
            return request_book[param]

    @staticmethod
    def filter_queryset_by_store(
        queryset: QuerySet[item_models.Item], store: str
    ) -> QuerySet[item_models.Item]:
        """
        Функция возвращает отфильтрованный queryset товаров по одному магазину.

        :param queryset: queryset товаров
        :param store: магазин
        :return: отсортированный queryset товара.
        """
        try:
            items = queryset.filter(store__slug=store)
        except ObjectDoesNotExist:
            items = queryset

        return items

    @staticmethod
    def filter_queryset_by_price(
        queryset: QuerySet[item_models.Item], price: str
    ) -> QuerySet[item_models.Item]:
        """
        Функция возвращает отфильтрованный queryset товаров по диапазону цен.

        :param queryset: queryset товаров
        :param price: диапазон цен
        :return: отсортированный queryset товара.
        """
        try:
            price_min = int(price.split(";")[0])
            price_max = int(price.split(";")[1])
            items = queryset.filter(price__range=(price_min, price_max))
        except ObjectDoesNotExist:
            items = queryset

        return items

    @staticmethod
    def get_available(
        queryset: QuerySet[item_models.Item],
    ) -> QuerySet[item_models.Item]:
        """Функция возвращает queryset доступных товаров."""
        queryset = queryset.filter(is_available=True)
        return queryset

    @staticmethod
    def make_get_param_dict(request: HttpRequest) -> dict:
        """
        Функиця создает словарь из всех параметров GET-запроса.

        Ключ записывает человеко-читаемое название параметра,
        в значение имя ключа из GET-запросов.
        """
        filter_dict = {
            "order_by": "отсортировано",
            "price": "цена",
            "color": "цвет",
            "title": "название",
            "page": "страница",
            "q": "запрос",
            "is_available": "в наличии",
            "store": "магазин",
            "cheep_first": "сначала дороже",
            "rich_first": "сначала дешевле",
            "best_seller": "лидеры продаж",
            "-created": "новинки",
            "by_comments": "по комментариям",
        }
        color_dict = {
            "red": "красный",
            "orange": "оранжевый",
            "yellow": "желтый",
            "green": "зеленый",
            "blue": "синий",
            "white": "белый",
            "black": "черный",
            "brown": "коричневый",
            "magenta": "фиолетовый",
        }
        query_string_dict = parse_qs(request.META.get("QUERY_STRING"))
        get_param_dict = {}
        feature_list = []
        for key, value in query_string_dict.items():
            if key not in filter_dict.keys() and value:
                # поиск по дополнительным характеристикам
                if len(value) > 1:
                    feature = (
                        item_models.FeatureValue.objects.prefetch_related(
                            "item_features"
                        ).filter(slug__in=value)
                    )
                    for feature_key in feature:
                        get_param_dict[
                            f"{feature_key.feature.title} - {feature_key.value}"
                        ] = feature_key.slug
                else:
                    feature = (
                        item_models.FeatureValue.objects.prefetch_related(
                            "item_features"
                        )
                        .filter(slug__in=value)
                        .first()
                    )
                    get_param_dict[
                        f"{feature.feature.title} - {feature.value}"
                    ] = feature.slug
                feature_list.append(feature)
            else:
                # поиск по цене
                if key == "price":
                    price_min, price_max = value[0].split(";")
                    get_param_dict[f"от ${price_min} до ${price_max}"] = key
                # поиск по цвету
                elif key == "color":
                    if len(request.GET.getlist("color")) == 1:
                        set_color = request.GET.getlist("color")[0].split(";")
                        value = value[0].split(";")
                    else:
                        set_color = request.GET.getlist("color")
                    for index, color in enumerate(set_color):
                        get_param_dict[color_dict[color]] = value[index]

                elif key == "order_by":
                    # сортировка
                    get_param_dict[filter_dict[value[0]]] = key
                elif key == "is_available":
                    # фильтр товаров по их наличию и доступности на сайте
                    get_param_dict["в наличии"] = key
                elif key == "page":
                    pass
                # поиск по названию
                elif key in ("q", "title") and len(value[0]) > 1:
                    get_param_dict[f'по запросу -"{value[0]}"'] = key
                elif key == "store":
                    get_param_dict[f"магазин - {value[0]}"] = key
                else:
                    get_param_dict[value[0]] = key
        return get_param_dict

    @staticmethod
    def smart_filter(
        request: HttpRequest, object_list: QuerySet, param_dict: dict
    ) -> QuerySet[item_models.Item]:
        """
        Функция  фильтрует товары по нескольким параметрам запроса.

        Каждый результат фильтрации добавляется в список.
        Итоговый список через лист-comprehension объединяется в один запрос.
        """
        filter_dict = {
            "order_by": "сортировка",
            "price": "цена",
            "color": "цвет",
            "title": "название",
            "page": "страница",
            "q": "запрос",
            "is_available": "в наличии",
            "store": "магазин",
        }
        query_get_param_dict = parse_qs(request.META.get("QUERY_STRING"))
        all_queryset_list = []
        object_list = (
            object_list.select_related("category", "store")
            .prefetch_related("tag", "views", "images", "feature_value")
            .filter(is_active=False)
        )

        for param, value in query_get_param_dict.items():
            if param in filter_dict.keys():
                if param == "title":
                    title = request.GET.get("title")
                    queryset = object_list.filter(title__icontains=title)
                    all_queryset_list.append(queryset)
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == "color":
                    color = query_get_param_dict.get("color")
                    if len(color) == 1:
                        color = query_get_param_dict.get("color")[0].split(";")
                    queryset = object_list.filter(color__in=color)
                    all_queryset_list.append(queryset)
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == "price":
                    price_range = request.GET.get("price", None)
                    min_price_queryset = int(
                        list(ItemHandler.get_range_price(object_list))[0]
                    )
                    max_price_queryset = int(
                        list(ItemHandler.get_range_price(object_list))[1]
                    )
                    min_price_request = int(price_range.split(";")[0])
                    max_price_request = int(price_range.split(";")[1])

                    if (
                        min_price_queryset != min_price_request
                        or max_price_queryset != max_price_request
                    ):
                        queryset = ItemHandler.filter_queryset_by_price(
                            object_list, price=price_range
                        )
                        if queryset.count() > 1:
                            all_queryset_list.append(queryset)
                    else:
                        del param_dict[
                            f"от ${min_price_request} до ${max_price_request}"
                        ]
                if param == "q":
                    query = str(request.GET.get("q"))
                    title = query.title()
                    lower = query.lower()
                    queryset = (
                        object_list.select_related("category", "store")
                        .prefetch_related(
                            "tag", "views", "images", "feature_value"
                        )
                        .filter(
                            Q(category__title__icontains=title)
                            | Q(title__icontains=title)
                            | Q(tag__title__icontains=title)
                            | Q(category__title__icontains=lower)
                            | Q(title__icontains=lower)
                            | Q(tag__title__icontains=lower)
                            | Q(store__title__icontains=lower)
                        )
                        .distinct()
                    )
                    if queryset.count() > 1:
                        all_queryset_list.append(queryset)
                if param == "order_by":
                    pass
            else:
                # поиск по спецификации конкретной категории товаров
                feature_value_list = query_get_param_dict[param]
                values_list = item_models.FeatureValue.objects.filter(
                    slug__in=feature_value_list
                ).values_list("id", flat=True)
                for v in values_list:
                    queryset = object_list.filter(feature_value=v)
                    all_queryset_list.append(queryset)

        if len(all_queryset_list) > 0:
            object_list = reduce(or_, [i for i in all_queryset_list])
        try:
            if query_get_param_dict["is_available"]:
                object_list = object_list.filter(is_available=True)
        except KeyError:
            object_list = object_list.distinct()

        return object_list.distinct()

    @staticmethod
    def item_detail_view(request, item) -> dict:
        """
        Функция возвращает context-словарь со данными по одному товару.

        Добавляет товар в список просмотренных товаров пользователя.
        Увеличивает количество просмотров товара.
        Возвращает теги, комментарии и характеристики товара.
        """
        user = request.user
        form = item_forms.CommentForm
        # добавляет товар в список просмотренных товаров пользователя
        try:
            AddItemToReview().add_item_to_review(user=user, item_id=item.id)
        except ObjectDoesNotExist:
            pass
        # увеличивает количество просмотров товара
        CountView().add_view(request, item_id=item.id)

        # список всех тегов товара
        tags = TagHandler.get_tags_queryset(item_id=item.id)

        # общее кол-во комментариев(прошедших модерацию) к товару
        comments_count = comment_services.CommentHandler.get_comment_cont(
            item.id
        )

        # все характеристики товара отсортированные по названию характеристик
        features = item.feature_value.order_by("feature__title")
        context = {
            "form": form,  # форма для создания комментария к товару
            "tags": tags,  # список тегов товара
            "item": item,  # товар (экземпляр класса Item)
            "features": features,  # список характеристик товара
            "comments_count": comments_count,  # счетчик кол-ва комментариев(прошедших модерацию)
        }
        return context

    @staticmethod
    def filter_list_view(
        request: HttpRequest,
        queryset: QuerySet[item_models.Item],
        paginate_by: int,
    ) -> dict:
        """Функция возвращает context-словарь с отфильтровапнными товарами."""
        object_list = queryset
        query_get_param_dict = ItemHandler.make_get_param_dict(request)
        object_list = ItemHandler.smart_filter(
            request, object_list, query_get_param_dict
        )
        related_category_list = CategoryHandler.get_related_category_list(
            object_list
        )

        if request.GET.get("order_by"):
            sort_by = request.GET.get("order_by")
            object_list = ItemHandler.ordering_items(
                queryset=object_list, order_by=sort_by
            )
        sort_message = ItemHandler.ordering_message(
            sort_param=request.GET.get("order_by")
        )
        #  формируем список  всех доступных цветов
        set_colors = get_colors(object_list)
        #  формируем queryset 10 самых популярных тегов
        set_tags = TagHandler.get_tags_queryset(
            object_list
        )  # для отображения 10 самых популярных тегов

        object_list = MixinPaginator(
            object_list, request, paginate_by
        ).my_paginator()  # пагинация результата
        context = {
            "object_list": object_list,
            "sort_message": sort_message,
            "set_colors": set_colors,
            "set_tags": set_tags,
            "related_category_list": related_category_list,
        }
        return context

    @staticmethod
    def store_list_view(request: HttpRequest, store, paginate_by: int) -> dict:
        """Функция возвращает context-словарь со всеми товарами одного магазина."""
        object_list = store.items.all()
        related_category_list = CategoryHandler.get_related_category_list(
            object_list
        )
        sort_message = f"товары магазина {store}"
        if request.GET.get("order_by"):
            object_list = ItemHandler.ordering_items(
                queryset=object_list, order_by=request.GET.get("order_by")
            )
            sort_message = ItemHandler.ordering_message(
                sort_param=request.GET.get("order_by")
            )
        object_list = MixinPaginator(
            object_list, request, paginate_by
        ).my_paginator()
        context = {
            "object_list": object_list,
            "related_category_list": related_category_list,
            "store": store,
            "sort_message": sort_message,
        }
        return context

    @staticmethod
    def get_alphabet_list() -> list:
        """
        Функция возвращает отфильтрованный список всех букв алфавита.

        Возвращается список всех букв алфавита существующих категорий.
        """
        return sorted(
            set(
                [
                    category.title[0]
                    for category in item_models.Category.objects.order_by(
                        "title"
                    )
                ]
            )
        )

    @staticmethod
    def create_item(instance, values: list, images):
        """Функция по обавлению к товару новых характеристик и изобрпажений."""
        for new_value in values:
            if new_value:
                feature = item_models.Feature.objects.filter(
                    values=new_value
                ).first()
                if feature:
                    if instance.feature_value.all():
                        for old_value in instance.feature_value.all():
                            if old_value.feature == feature:
                                instance.feature_value.remove(old_value)
                    instance.feature_value.add(new_value)
                    instance.save()

        for i in images:
            img = item_models.Image.objects.create(
                image=i, title=instance.title
            )
            if img not in instance.images.all():
                instance.images.add(img)
                instance.save()

    @staticmethod
    def update_item(item, images, tag_list, **kwargs):
        """Функция по редактированию тегов и изображений товара."""
        for t in tag_list:
            tag = item_models.Tag.objects.get(id=t.id)
            item.tag.add(tag)
            item.save()
        for img in images:
            image = item_models.Image.objects.create(
                image=img, title=item.title
            )
            item.images.add(image.id)
            item.save()
        store_id = kwargs["pk"]
        from app_store.services import store_services

        store = store_services.StoreHandler.get_store(store_id)
        store.items.add(item)
        store.save()

    @staticmethod
    def colors() -> list:
        """Функция возвращает все цвета доступные для товаров."""
        return [color[0] for color in item_models.Item.COLOURS]

    @staticmethod
    def admin_item_count() -> int:
        """Функция возвращает общее кол-во товаров на сайте для админ панели."""
        return (
            item_models.Item.objects.values_list("is_active", flat=True)
            .filter(is_active=False)
            .count()
        )


class TagHandler:
    """Класс для работы с тегами."""

    @staticmethod
    def get_tags_queryset(
        queryset=None, item_id: Union[int, None] = None
    ) -> QuerySet[item_models.Tag]:
        """
        Функция возвращает queryset-тегов.

        При наличии параметра отфильтрованный queryset-тегов.
        :param item_id: id-товара
        :param queryset: queryset-товаров
        :return: queryset-тегов
        """
        try:
            if queryset:
                tags = (
                    item_models.Tag.objects.prefetch_related("item_tags")
                    .filter(item_tags__in=queryset)
                    .annotate(item_count=Count("item_tags"))
                    .order_by("-item_count")
                )
            elif item_id:
                tags = item_models.Tag.objects.prefetch_related(
                    "item_tags"
                ).filter(item_tags=item_id)
            else:
                tags = item_models.Tag.objects.values_list("id", "title").all()
            return tags
        except ObjectDoesNotExist:
            raise Http404

    @staticmethod
    def get_tag(slug: str):
        """
        Функция возвращает один тег или ошибку 404.

        :param slug: slug-тега товара
        :return: тег или ошибку 404.
        """
        try:
            return item_models.Tag.objects.prefetch_related("item_tags").get(
                slug=slug
            )
        except ObjectDoesNotExist:
            raise Http404("такого тега не существует")

    @staticmethod
    def get_a_tag(tag_id):
        """
        Функция возвращает один тег или ошибку 404.

        :param tag_id: ID-тега
        :return: тег или ошибку 404.
        """
        return get_object_or_404(item_models.Tag, id=tag_id)

    @staticmethod
    def filter_queryset_by_tag(
        queryset: QuerySet[item_models.Item], tag: str
    ) -> QuerySet[item_models.Item]:
        """
        Функция возвращает queryset-товаров отфильтрованный по тегу.

        :param queryset: queryset товаров
        :param tag: тег по которому нужно отфильтровать
        :return: queryset товаров.
        """
        tag = TagHandler.get_tag(slug=tag)
        queryset = (
            queryset.select_related("category", "store")
            .prefetch_related("tag", "views", "images", "feature_value")
            .filter(tag=tag.id)
        )

        return queryset

    @staticmethod
    def get_abc_ordered() -> dict:
        """Функция возвращает словарь с отсортированными тегами по алфавиту."""
        tags = item_models.Tag.objects.all()
        tag_book = dict()
        abc = "ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
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

    @staticmethod
    def tag_list_view(
        request: HttpRequest,
        queryset: QuerySet[item_models.Item],
        paginate_by: int,
        tag: str,
    ) -> dict:
        """Функия возвращает context-словарь с товарами отфильтрованными по тегу."""
        #  фильтруем товары по переданному тегу
        object_list = TagHandler.filter_queryset_by_tag(queryset, tag=tag)
        # формируем список из связанных категорий или дочерних категорий
        related_category_list = CategoryHandler.get_related_category_list(
            object_list
        )
        #  находим экземпляр класса Tag по slug
        tag = TagHandler.get_tag(tag)
        #   формируем сообщение по типе фильтрации
        sort_message = f"по тегу {tag}"
        #  формируем список из связанных тегов
        set_tags = TagHandler.get_tags_queryset(object_list)
        # 9  сортируем полученный queryset по GET-параметру 'order_by'
        if request.GET.get("order_by"):
            object_list = ItemHandler.ordering_items(
                queryset=object_list, order_by=request.GET.get("order_by")
            )
            sort_message = ItemHandler.ordering_message(
                sort_param=request.GET.get("order_by")
            )
        # 10  пагинация результата
        object_list = MixinPaginator(
            object_list, request, paginate_by
        ).my_paginator()
        context = {
            "related_category_list": related_category_list,  # все категории в которых есть тег
            "tag": tag,  # один выбранный тег (при GET-запросе)
            "set_tags": set_tags,  # связанные теги
            "object_list": object_list,  # queryset товаров
            "sort_message": sort_message,  # сообщение (вид сортировки, фильтрации и результат)
        }
        return context

    @staticmethod
    def admin_tag_count() -> int:
        """Функция возвращает общее кол-во тегов на сайте для админ панели."""
        return item_models.Tag.objects.count()


class CategoryHandler:
    """Класс для работы с категориями."""

    @staticmethod
    def get_categories(slug=None) -> QuerySet:
        """
        Функция возвращает queryset-категорий товаров.

        При наличии параметра отфильтрованный queryset-категорий.
        :param slug: slug-товара
        :return: queryset-категорий.
        """
        try:
            if slug:
                category = item_models.Category.objects.select_related(
                    "parent_category"
                ).get(slug=slug)
            else:
                category = item_models.Category.objects.select_related(
                    "parent_category"
                ).exclude(items=None)
            return category
        except ObjectDoesNotExist:
            raise Http404(
                "Не найдена ни одна категория товаров, соответствующий запросу"
            )

    @staticmethod
    def get_related_category_list(
        queryset: QuerySet,
    ) -> QuerySet[item_models.Category]:
        """
        Функция возвращает queryset всех категорий.

        Возвращаются категороии относящиеся к выбранным товарам.
        :return: queryset-категорий.
        """
        related_categories = (
            item_models.Category.objects.values_list(
                "parent_category__sub_categories", flat=True
            )
            .filter(items__in=queryset)
            .distinct()
        )
        related_categories = item_models.Category.objects.filter(
            id__in=related_categories
        )
        category = item_models.Category.objects.filter(
            items__in=queryset
        ).distinct()

        return related_categories if related_categories.exists() else category

    @staticmethod
    def get_related_items(queryset: QuerySet) -> QuerySet:
        """Функция возвращает смежные категории."""
        return (
            item_models.Category.objects.select_related("items")
            .filter(items__in=queryset)
            .values_list("id", flat=True)
            .distinct()
        )

    @staticmethod
    def get_a_category(category_id: int):
        """
         Функция возвращает одну категорию.

        :param category_id: ID-категории
        :return: экземпляр категории
        """
        return get_object_or_404(item_models.Category, id=category_id)

    @staticmethod
    def get_categories_in_items_set(
        items: QuerySet[item_models.Item],
    ) -> QuerySet[item_models.Category]:
        """
        Функция возвращает queryset-категорий переданных товаров.

        :param items: queryset-товаров
        :return:queryset-категорий.
        """
        items_id_tuple = set(items.values_list("category"))
        items_list = [item[0] for item in items_id_tuple]
        categories = item_models.Category.objects.select_related(
            "parent_category"
        ).filter(id__in=items_list)
        return categories

    @staticmethod
    def filter_items_by_category(
        queryset: QuerySet, category_slug: str
    ) -> QuerySet[item_models.Category]:
        """
         Функция возвращает queryset товаров отфильтрованной по категории.

        :param queryset: queryset товаров
        :param category_slug: slug каткгории
        :return: queryset товаров
        """
        category = item_models.Category.objects.values("id", "slug").get(
            slug=category_slug
        )
        queryset = (
            queryset.select_related(
                "category", "category__parent_category", "store"
            )
            .prefetch_related("tag", "views", "images", "feature_value")
            .filter(
                Q(category=category["id"])
                | Q(category__parent_category=category["id"])
            )
        )

        return queryset

    @staticmethod
    def category_list_view(request: HttpRequest, queryset, paginate_by: int, category: str):
        """
        Функция возвращает context-словарь.

        Возращается словарь со всеми данными товаров
        отфильтрованных по одной категории.
        :param request - HttpRequest,
        :param queryset - queryset товаров,
        :param paginate_by - число элементов на странице
        :param category - slug-категории
        """
        color = None

        #  создаем словарь всех параметров GET-запроса
        query_get_param_dict = ItemHandler.make_get_param_dict(request)

        #  фильтруем товары по переданной категории
        filter_items_by_category = CategoryHandler.filter_items_by_category(
            queryset, category
        )

        #  находим экземпляр класса Category по slug
        category = CategoryHandler.get_categories(category)

        #  фильруем QuerySet по категории и переданным параметрам в GET-запросе
        object_list = ItemHandler.smart_filter(
            request, filter_items_by_category, query_get_param_dict
        )

        #  определяем диапазон цен в выбранной категории товаров
        if not object_list.exists():
            (
                price_min_in_category,
                price_max_in_category,
            ) = ItemHandler.get_range_price(filter_items_by_category)
        else:
            (
                price_min_in_category,
                price_max_in_category,
            ) = ItemHandler.get_range_price(object_list)
        if request.GET.get("price"):
            price_range = request.GET.get("price", None)
            price_min = int(price_range.split(";")[0])
            price_max = int(price_range.split(";")[1])
        else:
            price_min, price_max = price_min_in_category, price_max_in_category

        #   формируем сообщение по типе фильтрации
        sort_message = f"по категории {category}"

        # 5  формируем список из связанных категорий или дочерних категорий
        related_category_list = CategoryHandler.get_related_category_list(
            object_list
        )

        #  формируем список  всех доступных цветов
        set_colors = get_colors(object_list)

        #   формируем queryset 10 самых популярных тегов
        set_tags = TagHandler.get_tags_queryset(object_list)

        #   сортируем полученный queryset по GET-параметру 'order_by'
        if request.GET.get("order_by"):
            object_list = ItemHandler.ordering_items(
                queryset=object_list, order_by=request.GET.get("order_by")
            )
            sort_message = ItemHandler.ordering_message(
                sort_param=request.GET.get("order_by")
            )

        #   пагинация результата
        object_list = MixinPaginator(
            object_list, request, paginate_by
        ).my_paginator()
        context = {
            "related_category_list": related_category_list,  # все категории в которых есть искомое слово
            "category": category,  # одна выбранная категория товара  (при GET-запросе)
            "set_tags": set_tags,  # 10 тегов
            "color": color,  # один(несколько) выбранный(х) (при GET-запросе)  цвет(ов)
            "set_colors": set_colors,  # набор цветов доступных в queryset  товаров
            "object_list": object_list,  # queryset товаров
            "price_min_in_category": price_min_in_category,
            "price_max_in_category": price_max_in_category,
            "price_min": price_min,  # минимальная выбранная (при GET-запросе) цена товаров
            "price_max": price_max,  # максимальная выбранная (при GET-запросе)  цена товаров
            "sort_message": sort_message,  # сообщение (вид сортировки, фильтрации и результат)
            "get_params": query_get_param_dict,  # словарь из всех параметров GET-запроса
        }
        return context

    @staticmethod
    def admin_category_count():
        """Функция возвращает общее кол-во категорий для админи панели."""
        return item_models.Category.objects.count()


class CountView:
    """Класс для работы с количеством просмотров страницы товара покупателями."""

    @staticmethod
    def fake_ip():
        """Функция для создания фейкового IP-адресса."""
        ip_number_list = [str(random.randint(0, 255)) for _ in range(4)]
        ip = ".".join(ip_number_list)
        return item_models.IpAddress.objects.create(ip=ip)

    @staticmethod
    def get_client_ip(request):
        """Функция для получения IP-адреса пользователя."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    @staticmethod
    def add_view(request, item_id):
        """Функция для добавления просмотров товара."""
        item = ItemHandler().get_item(item_id)
        ip = CountView.get_client_ip(request)
        if request.user.is_authenticated:
            ip_address, created = item_models.IpAddress.objects.get_or_create(
                user=request.user, ip=ip
            )
        else:
            try:
                (
                    ip_address,
                    created,
                ) = item_models.IpAddress.objects.get_or_create(ip=ip)
            except MultipleObjectsReturned:
                ip_address = CountView.fake_ip()
        if ip_address not in item.views.all():
            item.views.add(ip_address)


class AddItemToReview:
    """
    Класс для добавления товара в список просматриваемых пользователем.

    Определяет три самых популярный категории товаров у пользователя.
    """

    @staticmethod
    def _get_reviews_items(user) -> QuerySet[item_models.Item]:
        """
        Функция возвращает queryset товаров.

        Если пользователь аутентифицирован -
        queryset просмотренных товаров
        иначе - самые популярные товары
        """
        if user.is_authenticated:
            return user.profile.review_items.select_related("category").all()
        return ItemHandler.get_popular_items()

    @staticmethod
    def _get_favorite_category_list(all_reviewed_item) -> List[int]:
        """Функция возвращает список самых просматриваемых ID-категорий товаров."""
        favorite_category = (
            all_reviewed_item.values_list("category")
            .annotate(rating=Count("category"))
            .order_by("-rating")
        )
        favorite_category_list = [
            category_id[0]
            for category_id in favorite_category
            if category_id[0]
        ]
        return favorite_category_list

    @staticmethod
    def _get_min_price(category_id: int) -> float:
        """Функция возвращает самую низкую цену на товар в категории."""
        category = CategoryHandler.get_a_category(category_id)
        min_price = category.items.values_list("price", flat=True).aggregate(
            min_price=Min("price")
        )
        return float(min_price.get("min_price"))

    @staticmethod
    def _get_favorite_category_and_price_dict(
        favorite_category_list: List[int],
        category_list: QuerySet[item_models.Category],
    ) -> List[Dict[str, Union[str, float]]]:
        """Функция возвращает список из словарей(категория, цена)."""
        favorite_category = []
        for category_id in favorite_category_list:
            favorite_category.append(
                {
                    "category": category_list.get(id=category_id),
                    "price": AddItemToReview._get_min_price(
                        category_id=category_id
                    ),
                }
            )
        return favorite_category[:3]

    @staticmethod
    def get_best_price_in_category(user):
        """Функция возвращает самые популярные категории товаров у пользователя."""
        all_reviewed_item = AddItemToReview._get_reviews_items(user)
        cache.get_or_set("all_reviewed_item", all_reviewed_item, 60)
        all_category_list = CategoryHandler.get_categories()

        favorite_category_list = AddItemToReview._get_favorite_category_list(
            all_reviewed_item
        )
        cache.get_or_set("favorite_category_list", favorite_category_list, 60)
        favorite_category_best_price = (
            AddItemToReview._get_favorite_category_and_price_dict(
                favorite_category_list, all_category_list
            )
        )
        cache.get_or_set(
            "favorite_category_best_price", favorite_category_best_price, 60
        )
        return favorite_category_best_price

    @staticmethod
    def add_item_to_review(user, item_id: int) -> QuerySet[item_models.Item]:
        """
        Функция добавляет товар в список просмотренных.

        И обновляет список избранных категорий пользователя.
        :param user: пользователь
        :param item_id: id-товара
        :return: queryset товаров
        """
        item = ItemHandler.get_item(item_id)
        reviews = AddItemToReview._get_reviews_items(user)
        if item not in reviews:
            try:
                user.profile.review_items.add(item)
            except ObjectDoesNotExist:
                pass
        AddItemToReview.get_best_price_in_category(user)
        return reviews


class ImageHandler:
    """Класс для работы с изображениями товара."""

    @staticmethod
    def resize_uploaded_image(
        image, title, width, format_image, quality_image
    ):
        """
        Функция изменяет изображение.

        Возвращеся изобраджение с изменеными размерами, сжатое,
        переименнованное  и с необходимым расширением
        :param image: фаил изображения
        :param title: имя экземплара класса Image
        :param width: необходимай ширина изображения
        :param format_image: новый формат изображение
        :param quality_image: качество нового изображение
        :return: instance of InMemoryUploadedFile
        """
        img = PilImage.open(image)
        exif = None
        if "exif" in img.info:
            exif = img.info["exif"]
        random_str = "".join(
            [random.choice(list("12345ABCDF")) for x in range(6)]
        )
        name = "_".join([str(title), str(random_str)])
        width_percent = width / float(img.size[0])
        height_size = int((float(img.size[1]) * float(width_percent)))
        img = img.resize((width, height_size), PilImage.ANTIALIAS)
        output = BytesIO()
        if exif:
            img.save(
                output, format=format_image, exif=exif, quality=quality_image
            )
        else:
            img.save(output, format=format_image, quality=quality_image)
        output.seek(0)
        image = InMemoryUploadedFile(
            output,
            "ImageField",
            f"{name}.{format_image}",
            f"image/{format_image}",
            output.tell(),
            None,
        )
        return image


class QueryStringHandler:
    """Класс для работы со строкой GET-запроса."""

    @staticmethod
    def remove_param(query_string, param):
        """
        Функция по удалению параметра из GET-запросв.

        :param query_string: строка GET-запроса,
        :param param: параметр для удаления,
        :return: возвращает новую строку GET-запроса без параметра.
        """
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
            result = query_string[0] + "?" + path
        else:
            result = query_string[0]

        return result


class FeatureHandler:
    """Класс для работы с характеристиками товара."""

    @staticmethod
    def get_active_features() -> QuerySet[item_models.Feature]:
        """Функция возвращает ТОЛЬКО АКТИВНЫЕ характеристики товаров."""
        return item_models.Feature.objects.all()

    @staticmethod
    def get_all_features() -> QuerySet[item_models.Feature]:
        """Функция возвращает все характеристики товаров."""
        return item_models.Feature.all_objects.all()

    @staticmethod
    def get_a_feature(feature_id):
        """Функция возвращает одну характеристику по ID."""
        return get_object_or_404(item_models.Feature, id=feature_id)


class ValueHandler:
    """Класс для работы со значениями характеристик товара."""

    @staticmethod
    def get_all_values() -> QuerySet[item_models.FeatureValue]:
        """Функция возвращает все значения характеристик товаров."""
        return item_models.FeatureValue.all_objects.all()

    @staticmethod
    def get_active_values() -> QuerySet[item_models.FeatureValue]:
        """Функция возвращает ТОЛЬКО АКТИВНЫЕ значения характеристик товаров."""
        return item_models.FeatureValue.objects.all()

    @staticmethod
    def get_a_value(value_id):
        """Функция возвращает одну характеристику по ID."""
        return get_object_or_404(item_models.FeatureValue, id=value_id)


def get_colors(queryset: QuerySet) -> List[str]:
    """
    Функция возвращает все цвета, которые есть у выбранных товаров.

    :param queryset: queryset товаров,
    :return: список цветов всех выбранных товаров
    """
    try:
        colors = queryset.exclude(color=None).values("color").distinct()
        colors = list(colors.values("color"))
        colors_list = []
        for color in colors:
            for key, val in color.items():
                colors_list.append(val)
        colors = list(set(colors_list))
        return colors
    except ObjectDoesNotExist:
        return []