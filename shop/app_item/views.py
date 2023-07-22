"""
Модуль содержит классы-предстывления для работы с корзиной.

1. CategoryListView - класс-представление для списка товаров по категории,
2. TagListView  - класс-представление для списка товаров по тегу,
3. FilterListView - класс-представление для списка товаров по параметрам,
4. ItemDetail - класс-представление для страницы одного товара
5. ItemBestSellerList - класс-представление для списка товаров-бестселлеров,
6. ItemNewList - класс-представление для списка товаров-новинок,
7. ItemForYouList - класс-представление для списка персональынх товаров,
8. StoreItemList - класс-представление для списка товаров одного магазина,
9. DeleteComment - класс-представление для удаления комментария,
10. EditComment - класс-представление для редактирования комментария,
11. remove_param - функция для удаления параметра из GET-запроса.

"""
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.views import generic

# models
from app_item import models as item_models
from app_store import models as store_models

# forms
from app_item import forms as item_forms

# services
from app_cart.services import cart_services
from app_item.services import comment_services
from app_item.services import item_services

# others
from utils.my_utils import MixinPaginator, query_counter


class CategoryListView(generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка товаров по категориям."""

    model = item_models.Item
    paginate_by = 8
    template_name = "app_item/item_list.html"
    queryset = item_services.ItemHandler.get_all_items()

    @query_counter
    def get(self, request, category=None, **kwargs):
        """
        GET-функция рендерид страницу с каталогом товаров.

        Возвращает context-словарь с  queryset-товаров,
        queryset-тегов, словарь с цветами.
        отсортированный по выбранному параметру или
        все товары.
        :param request: HttpRequest
        :param category: категория товаров
        :return: context.
        """
        super().get(request, **kwargs)
        context = item_services.CategoryHandler.category_list_view(
            request, self.queryset, self.paginate_by, category
        )
        return render(request, self.template_name, context=context)


class TagListView(generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех товаров по тегам."""

    model = item_models.Item
    template_name = "app_item/item_list.html"
    queryset = item_services.ItemHandler.get_popular_items()
    paginate_by = 6

    def get(self, request, tag=None, *args, **kwargs):
        """
        GET-функция рендерид страницу с каталогом товаров.

        Возвращает context-словарь с queryset-товаров,
        queryset-тегов, словарь с цветами.
        отсортированный по тегу или
        все товары.
        :param request: HttpRequest
        :param tag: тег товара
        :return: context.
        """
        super(TagListView, self).get(request, *args, **kwargs)
        context = item_services.TagHandler.tag_list_view(
            request=request,
            queryset=self.queryset,
            paginate_by=self.paginate_by,
            tag=tag,
        )
        return render(request, self.template_name, context=context)


class FilterListView(generic.ListView, MixinPaginator):
    """Класс-представление для отображения отфильтрованных товаров."""

    model = item_models.Item
    template_name = "app_item/item_list.html"
    queryset = item_services.ItemHandler.get_all_items()
    paginate_by = 8

    def get(self, request, *args, **kwargs):
        """
        GET-функция рендерид страницу с каталогом товаров.

        Возвращает context-словарь с queryset-товаров,
        queryset-тегов, словарь с цветами.
        отсортированный по переданными GET-параметрам.
        :param request: HttpRequest
        :return: context.
        """
        super().get(request, *args, **kwargs)
        context = item_services.ItemHandler.filter_list_view(
            request=request,
            queryset=self.queryset,
            paginate_by=self.paginate_by,
        )
        return render(request, self.template_name, context=context)


class ItemDetail(generic.DetailView, generic.CreateView):
    """Класс-представление для отображения одного товара."""

    model = item_models.Item
    context_object_name = "item"
    template_name = "app_item/item_detail.html"
    form_class = item_forms.CommentForm

    def get(self, request, *args, **kwargs):
        """
        Get-функция для отображения одного товара.

        Добавляет товар к списку просмотренных товаров пользователя
        Добавляет IP-адрес пользователя к товару.
        Создает комментарий к товару.
        """
        item = self.get_object()
        context = cache.get(item.id)
        if context is None:
            # список всех  товаров (Item) в корзине
            item_in_cart = cart_services.get_items_in_cart(request)
            # список всех добавленных товаров (CartItem) в корзине
            cart_item = cart_services.get_cart_item(request, item)
            context = item_services.ItemHandler.item_detail_view(request, item)
            # количество всех добавленных в корзину товаров (CartItem)
            try:
                cart_item_quantity = cart_item.quantity
            except (AttributeError, ObjectDoesNotExist):
                cart_item_quantity = 0

            context["already_in_cart"] = item_in_cart
            context["cart_item_in_cart"] = cart_item
            context["already_in_cart_count"] = cart_item_quantity

        return self.render_to_response(context)

    def form_valid(self, form):
        """
        Функция валидации формы для создания комментария.

        :param form: форма для создания комментария
        :return: на страницу товара
        """
        item_id = self.kwargs["pk"]
        user = self.request.user
        data = self.request.POST
        comment_services.CommentHandler.add_comment(
            user=user, item_id=item_id, data=data
        )
        cache.delete(item_id)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"""
            {user.get_full_name()}, спасибо за комментарий. 
            После модерации он будет опубликован.
            """
        )
        return redirect(self.request.get_full_path())

    def form_invalid(self, form):
        """Функция инвалидации формы по созданию комментария."""
        super().form_invalid(form)
        messages.add_message(
            self.request,
            messages.ERROR,
            """
            Ошибка.Комментарий не был добавлен.
            Повторите отправку комментария.
            """
        )
        return redirect("app_item:item_detail", args=[self.request.pk])


class ItemBestSellerList(generic.ListView):
    """Класс-представление для отображения всех популярных товаров."""

    model = item_models.Item
    template_name = "app_item/best_seller/best_seller_list.html"
    queryset = item_services.ItemHandler.get_bestseller()
    paginate_by = 8


class ItemNewList(generic.ListView):
    """Класс-представление для отображения новинок."""

    model = item_models.Item
    template_name = "app_item/new_items/new_items.html"
    queryset = item_services.ItemHandler.get_new_item_list()
    paginate_by = 8


class ItemForYouList(generic.ListView, MixinPaginator):
    """Класс-представление для отображения персональных товаров."""

    model = item_models.Item
    template_name = "app_item/items_for_you/items_for_you.html"
    paginate_by = 8

    def get(self, request, *args, **kwargs):
        """
        GET-функция для отображения персональных предложений.

        :param request: HttpRequest
        :return: context
        """
        super().get(request, *args, **kwargs)
        context = item_services.ItemHandler.get_items_for_you(
            request=self.request, paginate_by=self.paginate_by
        )
        return render(request, self.template_name, context=context)


class StoreItemList(generic.DetailView, MixinPaginator):
    """Класс-представление для отображения  всех товаров в магазине."""

    model = store_models.Store
    template_name = "app_item/item_list.html"
    context_object_name = "store"
    paginate_by = 8

    def get(self, request, *args, **kwargs):
        """
        GET-функция рендерид страницу с каталогом товаров.

        :param request: HttpRequest
        :return: context
        """
        super().get(request, *args, **kwargs)
        context = item_services.ItemHandler.store_list_view(
            request=request,
            store=self.get_object(),
            paginate_by=self.paginate_by,
        )
        return render(request, self.template_name, context=context)


class DeleteComment(generic.DetailView):
    """Класс-представление для удаления комментария."""

    model = item_models.Item
    template_name = "app_item/item_detail.html"
    context_object_name = "item"
    message = "Комментарий удален."

    def get(self, request, *args, **kwargs):
        """
        Функция удаляет комментарий о товаре.

        :return: возвращает на страницу товара
        """
        comment_services.CommentHandler.delete_comment(
            user=request.user, comment_id=kwargs["comment_id"]
        )
        messages.add_message(self.request, messages.INFO, self.message)
        return redirect("app_item:item_detail", kwargs["pk"])


class EditComment(generic.UpdateView):
    """Класс-представление для редактирования комментария."""

    model = item_models.Comment
    context_object_name = "comments"
    template_name = "app_item/comments/comment_edit.html"
    form_class = item_forms.CommentForm

    def get(self, request, *args, **kwargs):
        """Get-функция для отображения формы редактирования."""
        comment = comment_services.CommentHandler.get_comment(
            comment_id=kwargs["comment_id"]
        )
        form = item_forms.CommentForm(instance=comment)
        context = {
            "form": form,
            "comments": comment
        }
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        """POST-функция для редактирования комментария."""
        comment = comment_services.CommentHandler.get_comment(
            comment_id=kwargs["comment_id"]
        )
        form = item_forms.CommentForm(request.POST, instance=comment)
        item_id = kwargs["pk"]
        if form.is_valid():
            comment.is_published = False
            comment.save(update_fields=["is_published"])

            messages.add_message(
                self.request,
                messages.SUCCESS,
                "Комментарий изменен.После модерации он будет опубликован.",
            )
            return redirect("app_item:item_detail", item_id)
        return render(
            request, self.template_name, {"form": form, "comments": comment}
        )


def remove_param(request: HttpRequest, param: str):
    """Функция для удаления параметров фильтра в строке GET-запроса."""
    query_string = request.META.get("HTTP_REFERER").split("?")
    result = item_services.QueryStringHandler.remove_param(query_string, param)
    return redirect(result)
