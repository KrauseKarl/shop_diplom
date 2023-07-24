"""
Модуль содержит классы-предстывления для работы с магазинами.

    1. SellerDashBoardView - для отображения панели продавца,
    классы-представления для работы с магазином:
        2. StoreList - для отображения списка магазинов,
        3. StoreDetail - для отображения одного магазина,
        4. StoreCreate - для отображения создания магазина,
        5. StoreUpdate - для отображения редакирования магазина,
    классы-представления для работы с товарами:
        6. ItemCreate - для создания товара,
        7. ItemUpdate - для редакирования товара,
        8. ItemDelete - для де(активации) товара,
    классы-представления для работы с тегами:
        9. TagList - для отображения списка тегов,
        10. AddTag - для добавления тега в карточку товара,
        11. RemoveTag - для удаления тега из карточки товара,
    классы-представления для работы с тегами:
        12. RemoveValue - для удаления значение характеристики товара,
    классы-представления для работы с изображением:
        13. DeleteImage - для удаления изображения из карточки товара,
        14. MakeImageAsMain - для выбора изображения главным,
    классы-представления для работы с заказами:
        15. DeliveryList - для отображения списка заказов,
        16. DeliveryDetail - для отображения одного заказа,
        17. DeliveryUpdate - для редактирования заказа,
        18. OrderItemUpdate - для редактирования товаров в заказе,
        19. SentPurchase - для отправки заказа,
    классы-представления для работы с комментариями:
        20. CommentList - для отображения списка комментариев.
        21. CommentDetail - для отображения одного комментария.
    функции для работы с фикстурами:
        22. export_data_to_csv - для экспорта данных из БД в CVS формат,
        23. import_data_from_cvs - для импорта данных в БД в CVS формат,
        24. handle_uploaded_file - для создания файла с фикстурами.
"""

import csv
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.db.models import Sum, Q
from django.http import Http404, HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic
from django.http import HttpResponse

# models
from app_item import models as itm
from app_order import models as orm
from app_store import models as stm

# services
from app_item.services import comment_services as com_src
from app_order.services import order_services as ord_src
from app_item.services import item_services as itm_src
from app_store.services import store_services as str_src

# forms
from app_order import forms as ord_frm
from app_store import forms as str_frm

# other
from utils.my_utils import MixinPaginator, SellerOnlyMixin
from app_order import tasks


class SellerDashBoard(SellerOnlyMixin, generic.TemplateView):
    """Класс-представление для отображения главной страницы продавца."""

    template_name = "app_store/dashboard.html"

    def get(self, request, *args, **kwargs):
        """GET-функция для рендеренга главной страницы продавца."""
        context = self.get_context_data(**kwargs)
        context["comments"] = com_src.CommentHandler.seller_stores_comments(
            request.user
        )
        context["orders"] = ord_src.SellerOrderHAndler.get_seller_order_list(
            request.user.id
        ).count()
        context["stores"] = str_src.StoreHandler.get_all_story_by_owner(
            request.user
        ).count()

        return self.render_to_response(context)


# STORE VIEWS #
class StoreList(SellerOnlyMixin, generic.ListView):
    """Класс-представление для отображения списка магазинов продавца."""

    model = stm.Store
    template_name = "app_store/store/store_list.html"
    context_object_name = "stores"

    def get_queryset(self):
        """Функция возвращает queryset магазинов."""
        owner = self.request.user
        queryset = str_src.StoreHandler.get_all_story_by_owner(owner)
        return queryset


class StoreDetail(UserPassesTestMixin, generic.DetailView, MixinPaginator):
    """Класс-представление для отображения одного магазина."""

    model = stm.Store
    template_name = "app_store/store/store_detail.html"
    context_object_name = "store"
    paginate_by = 7

    def test_func(self):
        """Функция проверяет прова на просмотр магазина."""
        user = self.request.user
        store = self.get_object()
        return True if user == store.owner else False

    def get(self, request, *args, category=None, **kwargs) -> HttpResponse:
        """
        Функция возвращает экземпляр магазина.

        :param request: HttpRequest
        :param category: категория товара
        :param kwargs: 'order_by' параметр сортировки товаров
        :return: response
        """
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        store = self.get_object()
        all_items = store.items.all()

        try:
            category_slug = kwargs["slug"]
            category = itm_src.CategoryHandler.get_categories(category_slug)
            items = all_items.filter(category=category)
        except (ObjectDoesNotExist, KeyError):
            items = all_items
        if request.GET.get("q"):
            query = str(request.GET.get("q"))  # [:-1]
            title = query.title()
            lower = query.lower()
            items = (
                all_items.select_related("category", "store")
                .prefetch_related("tag", "views", "images", "feature_value")
                .filter(
                    Q(title__icontains=title) |
                    Q(title__icontains=lower)
                )
                .distinct()
            )
        if request.GET.get("order_by", None):
            order_by = request.GET.get("order_by")
            items = str_src.StoreHandler.ordering_store_items(
                queryset=items, order_by=order_by
            )
            context["message"] = str_src.StoreHandler.ordering_message(
                order_by=order_by
            )
        categories = itm_src.CategoryHandler.get_categories_in_items_set(
            all_items
        )
        object_list = MixinPaginator(
            items, self.request, self.paginate_by
        ).my_paginator()
        total_profit = str_src.StoreHandler.total_profit_store(store)
        context["categories"] = categories
        context["object_list"] = object_list
        context["total_profit"] = total_profit

        return self.render_to_response(context)


class StoreCreate(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания магазина."""

    model = stm.Store
    template_name = "app_store/store/create_store.html"
    form_class = str_frm.CreateStoreForm

    def form_valid(self, form):
        """Функция валидации формы для создания магазина."""
        store = form.save()
        store.is_active = True
        store.owner = self.request.user
        store.save()
        return redirect("app_store:store_detail", store.pk)

    def form_invalid(self, form):
        """Функция инвалидации формы для создания магазина."""
        form = str_frm.CreateStoreForm(self.request.POST, self.request.FILES)
        messages.add_message(
            self.request,
            messages.ERROR,
            "Ошибка. Магазин не создан. Повторите попытку.",
        )
        return super().form_invalid(form)


class StoreUpdate(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для обновления магазина."""

    model = stm.Store
    template_name = "app_store/store/store_edit.html"
    context_object_name = "store"
    form_class = str_frm.UpdateStoreForm
    message = "Данные магазтина обновлены"

    def test_func(self):
        """Функция проверяет прова на редактирования магазина."""
        user = self.request.user
        store = self.get_object()
        return True if user == store.owner else False

    def get_success_url(self):
        """Функция возвращает url-адрес успешного выполнения."""
        store = self.get_object()
        return redirect("app_store:store_edit", store.pk)

    def form_valid(self, form):
        """Функция валидации формы для редактирования магазина."""
        form.save()
        messages.add_message(self.request, messages.SUCCESS, self.message)
        return self.get_success_url()

    def form_invalid(self, form):
        """Функция инвалидации формы для редактирования магазина."""
        messages.add_message(self.request, messages.ERROR, self.message)
        return super(StoreUpdate, self).form_invalid(form)


# ITEM VIEWS #
class ItemCreate(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания и добавления товара в магазин."""

    model = stm.Store
    template_name = "app_store/item/add_item.html"
    form_class = str_frm.AddItemImageForm
    second_form_class = str_frm.TagFormSet

    def get_context_data(self, **kwargs):
        """Функция возвращает context-словарь с данными для создания товара."""
        formset_tag = str_frm.TagFormSet(queryset=itm.Tag.objects.none())
        formset_image = str_frm.ImageFormSet(
            queryset=itm.Image.objects.none()
        )
        context = {
            "tag_formset": formset_tag,
            "image_formset": formset_image,
            "form": self.form_class,
            "store": self.get_object(),
            "colors": itm_src.ItemHandler.colors,
            "category_set": itm.Category.objects.all(),
        }
        return context

    def form_valid(self, form):
        """Функция валидации формы для создания товара."""
        with transaction.atomic():
            item = form.save(commit=False)
            item.is_active = True
            item.save()
            images = self.request.FILES.getlist("image")
            tag_list = form.cleaned_data.get("tag")
            itm_src.ItemHandler.update_item(
                item=item, images=images, tag_list=tag_list
            )
            messages.add_message(
                self.request, messages.SUCCESS, f"Товаре {item} создан"
            )
            messages.add_message(
                self.request,
                messages.INFO,
                """Новый товар еще не активирован."""
                """Активируйте товар на странице товара."""
            )
        return redirect("app_store:store_detail", self.kwargs["pk"])

    def form_invalid(self, form):
        """Функция инвалидации формы для создания товара."""
        form = str_frm.AddItemImageForm(self.request.POST, self.request.FILES)
        messages.add_message(
            self.request,
            messages.ERROR,
            "Ошибка. Товар не создан. Повторите попытку."
        )
        return super().form_invalid(form)


class ItemUpdate(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для обновления товара."""

    model = itm.Item
    template_name = "app_store/item/edit_item.html"
    form_class = str_frm.UpdateItemForm

    def test_func(self):
        """Функция проверяет прова на редактирования товара."""
        user = self.request.user
        item = self.get_object()
        return True if user == item.store.owner else False

    def get(self, *args, **kwargs):
        """Функция возвращает context-словарь для редактирования товара."""
        formset_tag = str_frm.TagFormSet(queryset=itm.Tag.objects.none())
        formset_image = str_frm.ImageFormSet(
            queryset=itm.Image.objects.none()
        )
        context = {
            "tag_formset": formset_tag,
            "image_formset": formset_image,
            "form": self.form_class,
            "colors": itm_src.get_colors(itm.Item.objects.all()),
            "item": self.get_object(),
        }
        return self.render_to_response(context=context)

    def form_valid(self, form):
        """Функция валидации формы для редактирования товара."""
        instance = self.get_object()
        values = self.request.POST.getlist("value")
        images = self.request.FILES.getlist("image")
        data = self.request.POST
        form = str_frm.UpdateItemForm(
            data=data,
            instance=instance,
        )
        form.save()
        itm_src.ItemHandler.create_item(
            instance=instance, values=values, images=images
        )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"Данные о товаре {instance} обновлены"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Функция валидации формы для редактирования товара."""
        form = str_frm.UpdateItemForm(self.request.POST, self.request.FILES)
        messages.add_message(
            self.request, messages.ERROR, "Ошибка.Товар не обновлен."
        )
        return super().form_invalid(form)

    def get_success_url(self):
        """Функция возвращает url-адрес успешного выполнения."""
        item = self.get_object()
        store_id = item.store.id
        return reverse("app_store:store_detail", kwargs={"pk": store_id})


class ItemDelete(UserPassesTestMixin, generic.DeleteView):
    """Класс-представление для удаления/воостановления товара."""

    model = itm.Item

    def test_func(self):
        """Функция проверяет прова на удаления/воостановления товара."""
        user = self.request.user
        item = self.get_object()
        return True if user == item.store.owner else False

    def get(self, request, *args, **kwargs):
        """GET-функция для удаления/воостановления товара."""
        try:
            item = itm.Item.objects.get(id=kwargs["pk"])
            if item.is_active:
                item.is_active = False
                item.is_available = True
                message = f"Товар {item} успешно восстановлен"
            else:
                item.is_active = True
                item.is_available = False
                message = f"Товар {item} успешно удален"
            item.save(update_fields=["is_available", "is_active"])
            messages.add_message(self.request, messages.WARNING, message)
            return redirect("app_store:edit_item", item.pk)
        except ObjectDoesNotExist:
            raise Http404("Такой товар не существует")


# TAG VIEWS #
class TagList(SellerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка тегов товаров."""

    model = itm.Tag
    template_name = "app_store/tag/tag_list.html"
    paginate_by = 20

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        GET-функция для рендеренга страницы с тегами.

        Отображает список тегов
        с сортировкой их по алфовиту и
        строкой поиска.
        """
        alphabet_list = sorted(
            set(
                [tag.title[0] for tag in itm.Tag.objects.order_by("title")]
            )
        )
        sort_by_letter = request.GET.get("sort_by_letter")
        if sort_by_letter:
            tag_set = itm.Tag.objects.filter(
                title__istartswith=sort_by_letter
            )
        else:
            tag_set = itm.Tag.objects.all()
        object_list = MixinPaginator(
            tag_set, self.request, self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list, "alphabet": alphabet_list}
        return render(request, self.template_name, context)


class AddTag(SellerOnlyMixin, generic.UpdateView):
    """Класс-представление для добавления тега в карточку товара."""

    model = itm.Item
    context_object_name = "item"
    template_name = "app_store/tag/add_tag.html"
    form_class = str_frm.AddTagForm
    MESSAGE = "Новый тег(и) успешно добавлен(ы)"

    def form_valid(self, form):
        """Функция валидации формы для добавления тега к товару."""
        tag_list = form.cleaned_data.get("tag")
        item = itm.Item.objects.get(id=self.kwargs["pk"])
        for t in tag_list:
            tag = itm.Tag.objects.get(id=t.id)
            item.tag.add(tag)
            item.save()
        messages.add_message(self.request, messages.INFO, self.MESSAGE)
        return redirect("app_store:edit_item", item.pk)

    def form_invalid(self, form):
        """Функция инвалидации формы для добавления тега к товару."""
        messages.add_message(self.request, messages.ERROR, f"{form.errors}")
        return self.render_to_response(self.get_context_data(form=form))


class RemoveTag(generic.DeleteView):
    """Класс-представление для удаления тега из карточки товара."""

    model = itm.Tag

    def get(self, request, *args, **kwargs):
        """Функция удаления тега из карточки товара."""
        item_id = kwargs["item_id"]
        item = itm.Item.objects.get(id=item_id)
        tag_id = kwargs["tag_id"]
        tag = itm.Tag.objects.get(id=tag_id)
        if tag in item.tag.all():
            item.tag.remove(tag)
        item.save()
        messages.add_message(
            self.request, messages.WARNING, f"Тег {tag} успешно удален"
        )
        return redirect("app_store:edit_item", item.pk)


# FEATURE VALUE
class RemoveValue(UserPassesTestMixin, SellerOnlyMixin, generic.DeleteView):
    """Класс-представление для удаления значение характеристики товара."""

    model = itm.Item
    MESSAGE = "Значение характеристики удалено."

    def test_func(self):
        """Функция проверяет прова на удаления значение характеристики."""
        user = self.request.user
        item = self.get_object()
        owner = item.store.owner
        return True if user == owner else False

    def get(self, request, *args, **kwargs):
        """Функция для удаления значение характеристики товара."""
        item = self.get_object()
        value = itm.FeatureValue.objects.get(slug=kwargs['slug'])
        if value in item.feature_value.all():
            item.feature_value.remove(value)
        item.save()
        messages.add_message(self.request, messages.WARNING, self.MESSAGE)

        return redirect('app_store:edit_item', item.pk)


# IMAGE VIEWS #
class DeleteImage(UserPassesTestMixin, SellerOnlyMixin, generic.DeleteView):
    """Класс-представление для удаления изображения из карточки товара."""

    model = itm.Image
    MESSAGE = "Изображение успешно удалено"

    def test_func(self):
        """Функция проверяет прова на удаления изображения."""
        user = self.request.user
        image = self.get_object()
        owner = image.item_images.first().store.owner
        return True if user == owner else False

    def get(self, request, *args, **kwargs):
        """Функция для удаления изображения из карточки товара."""
        image = self.get_object()
        item = image.item_images.first()
        if image in item.images.all():
            item.images.remove(image)
            itm.Image.objects.filter(id=image.id).delete()
        item.save()
        messages.add_message(self.request, messages.WARNING, self.MESSAGE)
        return redirect("app_store:edit_item", item.pk)


class MakeImageAsMain(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для выбора изображения главным."""

    model = itm.Image
    MESSAGE = "Изображение выбранно как гланое"

    def test_func(self):
        """Функция проверяет прова на управление изображением."""
        user = self.request.user
        image = self.get_object()
        owner = image.item_images.first().store.owner
        return True if user == owner else False

    def get(self, request, *args, **kwargs):
        """Функция определяет изображение главным."""
        image = self.get_object()
        item = image.item_images.first()
        if image in item.images.all():
            for img in item.images.all():
                if img == image:
                    image.main = True
                    image.save()
                else:
                    if img.main:
                        img.main = False
                        img.save()
        item.save()
        messages.add_message(self.request, messages.WARNING, self.MESSAGE)
        return redirect("app_store:edit_item", item.pk)


# DELIVERY VIEWS #
class DeliveryList(SellerOnlyMixin, generic.ListView):
    """Класс-представление для отображения списка всех заказов продавца."""

    model = orm.Order
    template_name = "app_store/delivery/delivery_list.html"
    context_object_name = "orders"
    STATUS_LIST = orm.Order().STATUS
    paginate_by = 4

    def get_queryset(self):
        """Функция возвращает queryset заказов."""
        queryset = ord_src.SellerOrderHAndler.get_seller_order_list(
            owner=self.request.user
        )
        return queryset

    def get(self, request, status=None, **kwargs):
        """GET-функция для отображения списка всех заказов продавца."""
        super().get(request, **kwargs)
        object_list = self.get_queryset()
        if self.request.GET:
            # STORE
            if self.request.GET.get("stores"):
                stores = self.request.GET.getlist("stores")
                object_list = object_list.filter(store__title__in=stores)
            # STATUS
            if self.request.GET.get("status"):
                status = self.request.GET.getlist("status")
                object_list = object_list.filter(status__in=status)
            # SEARCH
            if self.request.GET.get("search"):
                search = self.request.GET.get("search")
                object_list = object_list.filter(id=search)
        object_list = MixinPaginator(
            request=request, object_list=object_list, per_page=self.paginate_by
        ).my_paginator()
        context = {
            "object_list": object_list,
            "stores": request.user.store.all(),
            "status_list": self.STATUS_LIST,
        }
        return render(request, self.template_name, context=context)


class DeliveryDetail(
    SellerOnlyMixin, UserPassesTestMixin, generic.DetailView
):
    """Класс-представление для отображения одного заказа в магазине."""

    model = orm.Order
    template_name = "app_store/delivery/delivery_detail.html"
    context_object_name = "order"
    STATUS_LIST_ORDER = orm.Order().STATUS
    STATUS_LIST_ITEM = orm.OrderItem().STATUS

    def test_func(self):
        """Функция проверяет прова на просмотр заказа."""
        user = self.request.user
        order = self.get_object()
        return True if user == order.store.first().owner else False

    def get(self, request, *args, category=None, **kwargs):
        """GET-функция для рендеринга одног заказа."""
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        stores = request.user.store.all()
        order = self.get_object()
        context["items"] = order.order_items.filter(
            item__item__store__in=stores
        )
        context["total"] = (
            context["items"].aggregate(
                total_cost=Sum("total")).get("total_cost")
        )
        context["status_list"] = self.STATUS_LIST_ORDER
        context["status_list_item"] = self.STATUS_LIST_ITEM
        return self.render_to_response(context)


class DeliveryUpdate(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для редактирования заказа."""

    model = orm.Order
    template_name = "app_store/delivery/delivery_edit.html"
    context_object_name = "order"
    form_class = ord_frm.OrderItemUpdateForm
    MESSAGE_SUCCESS = "Данные заказа успешно обновлены"
    MESSAGE_ERROR = "Ошибка обновления данных заказа"

    def test_func(self):
        """Функция проверяет прова на редактирования заказа."""
        user = self.request.user
        order = self.get_object()
        return True if user == order.store.first().owner else False

    def form_valid(self, form):
        """Функция валидации формы для редактирования заказа."""
        form.save()
        order = self.get_object()
        messages.add_message(
            self.request, messages.SUCCESS, self.MESSAGE_SUCCESS
        )
        return redirect("app_store:delivery_detail", order.pk)

    def form_invalid(self, form):
        """Функция инвалидации формы для редактирования заказа."""
        messages.add_message(
            self.request, messages.ERROR, self.MESSAGE_ERROR
        )
        return self.render_to_response(self.get_context_data(form=form))


class OrderItemUpdate(generic.UpdateView):
    """Класс-представление для обновления кол-во товаров в заказе."""

    model = orm.OrderItem
    template_name = "app_store/delivery/delivery_edit.html"
    form_class = ord_frm.OrderItemUpdateForm
    context_object_name = "order_item"
    MESSAGE_SUCCESS = "Количество товара обновлено."
    MESSAGE_ERROR = "Произошла ошибка при обновлении количества товара."

    def form_valid(self, form):
        """Функция валидации формы для редактирования заказа."""
        ord_src.SellerOrderHAndler.update_item_in_order(
            self.request, form
        )
        messages.add_message(
            self.request, messages.SUCCESS, self.MESSAGE_SUCCESS
        )
        return redirect("app_store:order_item_edit", self.get_object().pk)

    def form_invalid(self, form):
        """Функция инвалидации формы для редактирования заказа."""
        order_item = self.get_object()
        messages.add_message(
            self.request, messages.ERROR, self.MESSAGE_ERROR
        )
        return redirect("app_store:order_item_edit", order_item.pk)


class SentPurchase(SellerOnlyMixin, generic.UpdateView):
    """Класс-представление для отправки товара покупателю."""

    model = orm.OrderItem
    template_name = "app_store/delivery/delivery_detail.html"
    context_object_name = "order"
    form_class = str_frm.UpdateOrderStatusForm
    MESSAGE_ERROR = "Произошла ошибка при отправки заказа."

    def form_valid(self, form):
        """Функция валидации формы для отправки товара покупателю."""
        super().form_invalid(form)
        form.save()
        status = form.cleaned_data["status"]
        order_item_id = self.kwargs["pk"]
        order_item = ord_src.SellerOrderHAndler.sent_item(
            order_item_id, status
        )
        tasks.check_order_status.delay(order_item.order.id)
        messages.add_message(
            self.request, messages.SUCCESS, f"{order_item} отправлен"
        )
        return redirect(self.request.META.get("HTTP_REFERER"))

    def form_invalid(self, form):
        """Функция инвалидации формы для отправки товара покупателю."""
        messages.add_message(
            self.request, messages.ERROR, self.MESSAGE_ERROR
        )
        return super().form_invalid(form)


class CommentList(SellerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка комментариев продавца."""

    model = itm.Comment
    template_name = "app_store/comments/comment_list.html"
    context_object_name = "comments"
    paginate_by = 5

    def get(self, request, status=None, **kwargs):
        """GET-функция отображает список комментариев продавца."""
        super().get(request, **kwargs)
        object_list = ord_src.SellerOrderHAndler.get_seller_comment_list(
            user=request.user, param=request.GET
        )
        object_list = MixinPaginator(
            object_list, self.request, self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list}
        return render(request, self.template_name, context)


class CommentDetail(generic.DetailView):
    """Класс-представление для отображения одного комментария."""

    model = itm.Comment
    template_name = "app_store/comments/comment_detail.html"
    context_object_name = "comment"


# EXPORT & IMPORT DATA-STORE FUNCTION #
def export_data_to_csv(*args, **kwargs):
    """Функция для экспорта данных из магазина продавца в формате CSV."""
    store_id = kwargs["pk"]
    store = stm.Store.active_stores.get(id=store_id)
    items = itm.Item.objects.filter(store__id=store_id)
    curr_date = datetime.now().strftime("%Y-%m-%d")
    response = HttpResponse()
    response[
        "Content-Disposition"
    ] = f'attachment; filename="price_list_{curr_date}({store.title})"'
    writer = csv.writer(response)
    # writer.writerow(['id', 'title', 'stock', 'price'])
    items_report = items.values_list(
        "id",
        "title",
        "stock",
        "price",
        "is_available",
        "category__id",
        "store__id",
        "color",
    )
    for item in items_report:
        writer.writerow(item)
    return response


def import_data_from_cvs(request, **kwargs):
    """Функция для импорта данных в магазин продавца."""
    store = kwargs["pk"]
    if request.method == "POST" and request.FILES["file"]:
        # allowed_types = ['.cvs', ]
        form = str_frm.ImportDataFromCVS(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.cleaned_data.get("file")
            file_name = upload_file.name.split(".")[0]
            handle_uploaded_file(upload_file, file_name)
            with open(
                    f"fixtures/{file_name}.txt", "r", encoding="utf-8"
            ) as file:
                reader = csv.reader(file)
                for row in reader:
                    category = itm.Category.objects.filter(id=row[5]).first()
                    store = stm.Store.objects.filter(id=row[6]).first()
                    _, created = itm.Item.objects.update_or_create(
                        id=row[0],
                        title=row[1],
                        defaults={
                            "stock": row[2],
                            "price": row[3],
                            "is_available": row[4],
                            "category": category,
                            "store": store,
                            "color": row[7],
                        },
                    )
                messages.add_message(
                    request, messages.SUCCESS, "Фикстуры успешно загружены."
                )
            return redirect("app_store:store_detail", store.id)
        else:
            return redirect("app_store:store_detail", store.id)


def handle_uploaded_file(f, name):
    """Функция создания файла с фикстурами."""
    with open(f"fixtures/{name}.txt", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
