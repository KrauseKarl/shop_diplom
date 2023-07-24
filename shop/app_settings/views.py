"""
Модуль содержит классы-предстывления для работы с настроками сайта.

    классы-представления для работы с панели управления администратора:

    1. AdminDashBoardView - отображения панели администратора,
    2. SettingsView - отображения сновных настороек сайта,
    3. SettingsUpdatedView - редактирования сновных настороек сайта,

    классы-представления для работы с пользователями:

    4. CustomerListView - для списка покупателей,
    5. CustomerDeleteView - для (де)активации покупатель,
    6. SellerListView - для списока продавцов,
    7. SellerDeleteView - для (де)активации продавцов,
    8. StoreListView - для списока магазинов,
    9. ProductListView - для списка тоаров,

    классы-представления для работы с категориями:

    10. CategoryListView - для списка категорий,
    11. CategoryCreateView - для создания категории,
    12. CategoryUpdateView - для редактировании категории,
    13. CategoryDeleteView - для (де)активации каетгории,

    классы-представления для работы с тегами:

    14. TagListView - для списка тегов,
    15. TagCreateView - для создания тега,
    16. TagUpdateView - для редактировании тега,
    17. TagDeleteView - для (де)активации тега,

    классы-представления для работы с характеристиками:

    18. FeatureListView - для списка характеристик,
    19. FeatureCreateView - для создания характеристики,
    20. FeatureUpdateView - для редактировании характеристики,
    21. FeatureDeleteView - для (де)активации характеристики,
    22. ValueCreateView - для создания значения характеристики,

    классы-представления для работы с комментариями:

    23. CommentListView - для списка комментариев,
    24. CommentDetail - для одного комментария,
    25. CommentDelete - для удаления комментария,
    26. CommentModerate - для модерациия комментария,

    классы-представления для работы с заказами:

    27.OrderListView - для списка заказов,
    28.OrderDetailView - для одного заказа.
"""
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Count, Q
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse, Http404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

# models
from app_item import models as item_models
from app_settings import models as settings_modals
from app_order import models as order_models
from app_user import models as auth_modals
from app_store import models as store_modals

# forms
from app_settings import forms as admin_forms
from app_settings import forms as settings_form

# services
from app_item.services import comment_services
from app_order.services import order_services
from app_item.services import item_services
from app_store.services import store_services

# other
from utils.my_utils import AdminOnlyMixin, MixinPaginator


class AdminDashBoardView(AdminOnlyMixin, generic.TemplateView):
    """Класс-представление для отображения панели  администратора."""

    template_name = "app_settings/admin/dashboard.html"

    def get(self, request, *args, **kwargs):
        """Функция возвращает context-словарь с данными панели администратора."""
        context = self.get_context_data(**kwargs)
        context[
            "categories"
        ] = item_services.CategoryHandler.admin_category_count()
        context[
            "comments_count"
        ] = comment_services.CommentHandler.non_moderate_comments_amount()
        context["customer"] = auth_modals.Profile.objects.filter(
            user__groups__name="customer"
        ).count()
        context["items"] = item_services.ItemHandler.admin_item_count()
        context["orders"] = order_services.AdminOrderHAndler.orders_count()
        context["seller"] = auth_modals.Profile.objects.filter(
            user__groups__name="seller"
        ).count()
        context["stores"] = store_services.AdminStoreHandler.stores_count()
        context["tags"] = item_services.TagHandler.admin_tag_count()

        return self.render_to_response(context)


class SettingsView(AdminOnlyMixin, generic.TemplateView):
    """Класс-представление для отображения сновных настороек сайта."""

    template_name = "app_settings/admin/settings.html"


class SettingsUpdatedView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для редактирования сновных настороек сайта."""

    model = settings_modals.SiteSettings
    template_name = "app_settings/admin/settings_edit.html"
    form_class = admin_forms.UpdateSettingsForm
    MESSAGE_SUCCESS = "Настройки обновлены"
    MESSAGE_ERROR = "Ошибка. Настройки не обновлены."

    def form_valid(self, form):
        """Функция валидации формы для реадактирования настроек."""
        form.save()
        messages.add_message(
            self.request, messages.SUCCESS, self.MESSAGE_SUCCESS
        )
        return redirect("app_settings:dashboard")

    def form_invalid(self, form):
        """Функция инвалидации формы для реадактирования настроек."""
        messages.add_message(
            self.request, messages.ERROR, self.MESSAGE_ERROR
        )
        return super().form_invalid(form)


class CustomerListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списка покупателей."""

    model = auth_modals.User
    template_name = "app_settings/customer/customer_list.html"
    paginate_by = 4

    def get_queryset(self):
        """Функция возвращает queryset покупателей."""
        queryset = (
            auth_modals.User.objects.filter(groups__name="customer")
            .annotate(amount=Count("user_order"))
            .order_by("-amount")
        )
        return queryset

    def get(self, request, *args, **kwargs):
        """GET-функция для рендеренга списка покупателей."""
        object_list = self.get_queryset()
        if self.request.GET:
            if self.request.GET.get("search"):
                search = str(self.request.GET.get("search")).title()
                object_list = object_list.filter(
                    Q(first_name__startswith=search) |
                    Q(last_name__startswith=search)
                )
        object_list = MixinPaginator(
            object_list, self.request, self.paginate_by
        ).my_paginator()
        context = {
            "object_list": object_list
        }
        return render(self.request, self.template_name, context=context)


class CustomerDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для блокировки/разблокировки покупатель."""

    model = auth_modals.User

    def get(self, request, *args, **kwargs):
        """GET-функция для блокировки/разблокировки покупатель."""
        customer_id = kwargs["pk"]
        try:
            customer = auth_modals.User.objects.get(id=customer_id)
            customer_name = customer.get_full_name()
            if customer.profile.is_active:
                customer.profile.is_active = False
                message = f"Покупатель {customer_name} разблокирован"
            else:
                customer.profile.is_active = True
                message = f"Покупатель {customer_name} заблокирован"
            customer.profile.save()
            messages.add_message(self.request, messages.WARNING, message)
            return redirect("app_settings:customer_list")
        except ObjectDoesNotExist:
            raise Http404("Такого покупателя не существует.")


class SellerListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списока продавцов."""

    model = auth_modals.User
    template_name = "app_settings/seller/seller_list.html"
    paginate_by = 4

    def get_queryset(self):
        """Функция возвращает queryset продавцов."""
        queryset = auth_modals.User.objects.filter(groups__name="seller")
        return queryset

    def get(self, request, *args, **kwargs):
        """GET-функция для рендеренга списка покупателей."""
        object_list = self.get_queryset()
        if self.request.GET:
            if self.request.GET.get("search"):
                search = self.request.GET.get("search")
                object_list = object_list.filter(
                    Q(first_name__startswith=search) |
                    Q(last_name__startswith=search)
                )
        object_list = MixinPaginator(
            object_list, self.request, self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list}
        return render(self.request, self.template_name, context=context)


class SellerDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для блокировки/разблокировки продавеца."""

    model = auth_modals.User

    def get(self, request, *args, **kwargs):
        """GET-функция для блокировки/разблокировки продавеца."""
        try:
            seller = auth_modals.User.objects.get(id=kwargs["pk"])
            seller_name = seller.get_full_name()
            if seller.profile.is_active:
                seller.profile.is_active = False
                message = f"Продавец {seller_name} заблокирован"
            else:
                seller.profile.is_active = True
                message = f"Продавец {seller_name} разблокирован "
            seller.profile.save()
            messages.add_message(
                self.request, messages.WARNING, message
            )
            return redirect("app_settings:seller_list")
        except ObjectDoesNotExist:
            raise Http404("Такого продавца не существует")


class StoreListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списка магазинов."""

    model = store_modals.Store
    template_name = "app_settings/store/store_list.html"
    paginate_by = 4
    queryset = store_modals.Store.objects.order_by("created")

    def get(self, request, *args, **kwargs):
        """GET-функция для рендеренга списка магазинов."""
        object_list = self.queryset
        if self.request.GET:
            if self.request.GET.get("search"):
                search = self.request.GET.get("search")
                object_list = object_list.filter(
                    Q(title__startswith=search) |
                    Q(owner__first_name__startswith=search)
                )
        object_list = MixinPaginator(
            object_list, self.request, self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list}
        return render(self.request, self.template_name, context=context)


class ProductListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списка товаров."""

    model = item_models.Item
    template_name = "app_settings/item/item_list.html"
    paginate_by = 4
    queryset = item_models.Item.objects.order_by("created")

    def get(self, request, *args, **kwargs):
        """GET-функция для рендеренга списка товаров."""
        object_list = self.queryset
        if self.request.GET:
            if self.request.GET.get("search"):
                search = self.request.GET.get("search")
                object_list = object_list.filter(
                    Q(title__startswith=search) | Q(id=search)
                )
        object_list = MixinPaginator(
            object_list, self.request, self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list}
        return render(self.request, self.template_name, context=context)


class CategoryListView(AdminOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка категорий товаров."""

    model = item_models.Category
    template_name = "app_settings/category/category_list.html"
    paginate_by = 5

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        GET-функция для рендеренга списка категорий товаров.

        Возвращаются все катгории или
        определенную категорию товаров,
        если передан параметр ['sort_by_letter'],
        так же возвращает отфильтрованный
        (по существующим категориям)
        список всех букв алфавита
        для быстрого поиска категорий по алфавиту.
        :param request: HttpRequest
        :param kwargs:  ['sort_by_letter'] параметр фильтрации
        :return: HttpResponse
        """
        alphabet_list = item_services.ItemHandler.get_alphabet_list()
        sort_by_letter = request.GET.get("sort_by_letter")
        category_title = request.GET.get("title")
        if sort_by_letter:
            categories = item_models.Category.objects.filter(
                title__istartswith=sort_by_letter
            )
        elif category_title:
            categories = item_models.Category.objects.filter(
                Q(title__icontains=category_title) |
                Q(title__istartswith=category_title)
            )
        else:
            categories = item_models.Category.objects.all()
        object_list = MixinPaginator(
            categories, self.request, self.paginate_by
        ).my_paginator()
        context = {
            "object_list": object_list,
            "alphabet": alphabet_list,
        }
        return render(request, self.template_name, context)


class CategoryCreateView(AdminOnlyMixin, generic.CreateView):
    """Класс-представление для создания категории товаров."""

    model = item_models.Category
    template_name = "app_settings/category/category_create.html"
    form_class = admin_forms.CreateCategoryForm
    extra_context = {
        "categories": item_models.Category.objects.filter(
            parent_category=None
        )
    }

    def form_valid(self, form):
        """Функция валидации формы для создания категории."""
        form.save()
        category_title = form.cleaned_data.get("title")
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"Категория - '{category_title}' создана"
        )
        return redirect("app_settings:category_list")


class CategoryUpdateView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для редактирования категории."""

    model = item_models.Category
    template_name = "app_settings/category/category_edit.html"
    form_class = admin_forms.UpdateCategoryForm

    def form_valid(self, form):
        """Функция валидации формы для редактирования категории."""
        form.save()
        category_title = form.cleaned_data.get("title")
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f"Категория - '{category_title}' обновлена"
        )
        return redirect("app_settings:category_list")

    def form_invalid(self, form):
        """Функция инвалидации формы для редактирования категории."""
        messages.add_message(
            self.request, messages.ERROR, "Ошибка обновлений."
        )
        return super(CategoryUpdateView, self).form_invalid(form)


class CategoryDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление (де)активации категории."""

    model = item_models.Category

    def get(self, request, *args, **kwargs):
        """GET-функция для (де)активации категории."""
        category = item_services.CategoryHandler.get_a_category(
            kwargs["pk"]
        )
        if category.is_archived:
            category.is_archived = False
            message = f"Категория {category} возращена из  архива"
        else:
            category.is_archived = True
            message = f"Категория {category} успешно удалена в архив"
        category.save()
        messages.add_message(self.request, messages.WARNING, message)
        return redirect("app_settings:category_list")


class TagListView(AdminOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка тегов товаров."""

    model = item_models.Tag
    template_name = "app_settings/tag/tag_list.html"
    paginate_by = 5
    queryset = item_models.Tag.all_objects.all()

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """GET-функция для рендеренга страницы со списком тегов."""
        object_list = self.get_queryset()
        if self.request.GET:
            if self.request.GET.get("search"):
                search = self.request.GET.get("search")
                object_list = object_list.filter(
                    title__startswith=search
                )
        object_list = MixinPaginator(
            object_list, self.request, self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list}
        return render(request, self.template_name, context)


class TagCreateView(AdminOnlyMixin, generic.CreateView):
    """Класс-представление для создания тега."""

    model = item_models.Category
    template_name = "app_settings/tag/tag_edit.html"
    form_class = settings_form.CreateTagForm

    def form_valid(self, form):
        """Функция валидации формы создания тега."""
        form.save()
        tag_title = form.cleaned_data.get("title").lower()
        messages.add_message(
            self.request, messages.SUCCESS, f'Тег - "{tag_title}" создан'
        )
        return redirect("app_settings:tag_list")

    def form_invalid(self, form):
        """Функция инвалидации формы создания тега."""
        form = settings_form.CreateTagForm(self.request.POST)
        return super(TagCreateView, self).form_invalid(form)


class TagUpdateView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для редактирования тега."""

    model = item_models.Tag
    template_name = "app_settings/tag/tag_edit.html"
    form_class = settings_form.CreateTagForm

    def form_valid(self, form):
        """Функция валидации формы редактирования тега."""
        form.save()
        tag_title = form.cleaned_data.get("title").upper()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f'Тег - "{tag_title}" изменен'
        )
        return redirect("app_settings:tag_list")

    def form_invalid(self, form):
        """Функция инвалидации формы редактирования тега."""
        form = settings_form.CreateTagForm(self.request.POST)
        return super(TagUpdateView, self).form_invalid(form)


class TagDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для (де)активации тега."""

    model = item_models.Tag

    def get(self, request, *args, **kwargs):
        """GET-функция для (де)активации тега."""
        try:
            tag = item_services.TagHandler.get_a_tag(
                tag_id=kwargs["pk"]
            )
            if tag.is_active:
                tag.is_active = False
                message = f"Тег - '{tag}' не активен"
            else:
                tag.is_active = True
                message = f"Тег - '{tag}' снова активен"
            tag.save(update_fields=["is_active"])
            messages.add_message(
                self.request, messages.WARNING, message
            )
            return redirect("app_settings:tag_list")
        except ObjectDoesNotExist:
            raise Http404("Такого тега не существует")


class FeatureListView(AdminOnlyMixin, generic.DetailView):
    """Класс-представление для отображения списка характеристик категории."""

    model = item_models.Category
    template_name = "app_settings/feature/feature_list.html"

    def get(self, request: HttpRequest, *args, **kwargs):
        """GET-функция для рендеренга списка характеристик категории."""
        super(FeatureListView, self).get(request, *args, **kwargs)
        category = self.get_object()
        features = item_models.Feature.all_objects.prefetch_related(
            "categories"
        ).filter(categories=category)
        values = item_models.FeatureValue.all_objects.select_related(
            "feature"
        ).filter(
            feature__in=features
        )
        context = {
            "features": features,
            "category": category,
            "values": values
        }
        return render(request, self.template_name, context)


class FeatureCreateView(AdminOnlyMixin, generic.CreateView):
    """Класс-представление для создания характеристики категории."""

    model = item_models.Feature
    template_name = "app_settings/feature/feature_create.html"
    form_class = settings_form.CreateFeatureForm

    def get(self, request, *args, **kwargs):
        """GET-функция возвращает context-словарь."""
        super().get(request, *args, **kwargs)
        context = {"category": self.kwargs["pk"]}
        return render(self.request, self.template_name, context)

    def form_valid(self, form):
        """Функция валидации формы для создания характеристики."""
        feature = form.save()
        category_id = self.kwargs.get("pk")
        category = item_services.CategoryHandler.get_a_category(
            category_id=category_id
        )
        feature.categories.add(category.id)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f'Характеристика - "{feature}" добавлено'
        )
        return redirect("app_settings:feature_list", category_id)

    def form_invalid(self, form):
        """Функция инвалидации формы для создания характеристики."""
        form = settings_form.CreateFeatureForm(self.request.POST)
        messages.add_message(
            self.request,
            messages.ERROR,
            f"Произошла ошибка - {form.errors}"
        )
        category_id = self.kwargs.get("pk")
        return redirect("app_settings:feature_create", category_id)


class FeatureUpdateView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для редактирования характеристики категории."""

    model = item_models.Feature
    template_name = "app_settings/feature/feature_edit.html"
    form_class = admin_forms.UpdateFeatureForm

    def form_valid(self, form):
        """Функция валидации формы для редактирования характеристики."""
        form.save()
        category_id = self.kwargs["category_id"]
        feature_title = form.cleaned_data.get("title")
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f'Характеристика - "{feature_title}" обновлена',
        )
        return redirect("app_settings:feature_list", category_id)

    def form_invalid(self, form):
        """Функция инвалидации формы для редактирования характеристики."""
        form = admin_forms.UpdateFeatureForm(self.request.POST)
        return super(FeatureUpdateView, self).form_invalid(form)


class FeatureDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для (де)активации характеристики категории."""

    model = item_models.Feature

    def get(self, request, *args, **kwargs):
        """GET-функция для (де)активации характеристики категории."""
        feature_id = kwargs["pk"]
        category_id = kwargs["category_id"]
        try:
            feature = item_services.FeatureHandler.get_a_feature(
                feature_id=feature_id
            )
            if feature.is_active:
                feature.is_active = False
                message = f"Характеристика - '{feature}' не активна"
            else:
                feature.is_active = True
                message = f"Характеристика - '{feature}' снова активна"
            feature.save(
                update_fields=[
                    "is_active",
                ]
            )
            messages.add_message(self.request, messages.WARNING, message)
            return redirect("app_settings:feature_list", category_id)
        except ObjectDoesNotExist:
            raise Http404("Такой характеристики не существует")


class ValueCreateView(AdminOnlyMixin, generic.CreateView):
    """Класс-представление для создания значения характеристики."""

    model = item_models.FeatureValue
    template_name = "app_settings/feature/value_create.html"
    form_class = settings_form.CreateValueForm

    def get(self, request, *args, **kwargs):
        """GET-функция context-словарь с данными."""
        super().get(request, *args, **kwargs)
        category_id = item_models.Category.objects.get(
            feature=self.kwargs["pk"]
        ).id
        context = {"category_id": category_id}
        return render(self.request, self.template_name, context)

    def form_valid(self, form):
        """Функция валидации формы для создания значения характеристики."""
        value = form.save(commit=False)
        feature = item_services.FeatureHandler.get_a_feature(
            feature_id=self.kwargs.get("pk")
        )
        value.feature = feature
        value.save()
        category = item_models.Category.objects.get(feature=feature)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f'Значение - "{value}" добавлено'
        )
        return redirect("app_settings:feature_list", category.id)

    def form_invalid(self, form):
        """Функция инвалидации формы для создания значения характеристики."""
        form = settings_form.CreateValueForm(self.request.POST)
        feature_id = self.kwargs.get("pk")
        messages.add_message(
            self.request, messages.ERROR, f"{form.errors.get('value')}"
        )
        return redirect("app_settings:value_create", feature_id)


class ValueDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для удаления значение характеристики категории."""

    model = item_models.FeatureValue

    def get(self, request, *args, **kwargs):
        """GET-функция для (де)активации значение характеристики."""
        value_id = kwargs["pk"]
        category_id = kwargs["category_id"]
        try:
            value = item_models.FeatureValue.all_objects.get(id=value_id)
            if value.is_active:
                value.is_active = False
                message = f"Характеристика - '{value}' не активна"
            else:
                value.is_active = True
                message = f"Характеристика - '{value}' снова активна"
            value.save(
                update_fields=[
                    "is_active",
                ]
            )
            messages.add_message(self.request, messages.WARNING, message)
            return redirect("app_settings:feature_list", category_id)
        except ObjectDoesNotExist:
            raise Http404("Такой характеристики не существует")


class CommentListView(AdminOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка комментариев."""

    model = item_models.Comment
    template_name = "app_settings/comment/comment_list.html"
    paginate_by = 4

    def get(self, request, *args, **kwargs):
        """GET-функция для рендеренга списка комментариев."""
        object_list = comment_services.CommentHandler.get_all_comments()
        if request.GET:
            if request.GET.get("new"):
                object_list = object_list.filter(is_published=False)
            elif request.GET.get("moderated"):
                object_list = object_list.filter(
                    Q(is_published=True) & Q(archived=False)
                )
            elif request.GET.get("archived"):
                object_list = object_list.filter(archived=True)
        object_list = MixinPaginator(
            request=request,
            object_list=object_list,
            per_page=self.paginate_by
        ).my_paginator()
        context = {"object_list": object_list}

        return render(request, self.template_name, context=context)


class CommentDetail(AdminOnlyMixin, generic.DetailView):
    """Класс-представление для отображения одного комментария."""

    model = item_models.Comment
    template_name = "app_settings/comment/comment_detail.html"
    context_object_name = "comment"


class CommentDelete(AdminOnlyMixin, generic.DeleteView):
    """Класс-представление для удаления комментария."""

    model = item_models.Comment
    template_name = "app_settings/comment/comment_delete.html"
    MESSAGE = "момментарий удален"

    def form_valid(self):
        """Функция для  удаления комментария."""
        self.object.archived = True
        self.object.save()
        messages.add_message(self.request, messages.WARNING, self.MESSAGE)
        return HttpResponseRedirect(self.object.get_absolute_url())


class CommentModerate(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для модерации комментария."""

    model = item_models.Comment
    template_name = "app_settings/comment/comment_update.html"
    fields = ["is_published"]
    success_url = reverse_lazy("app_settings:comments_list")


class OrderListView(generic.ListView):
    """Класс-представление для отображения списка заказов."""

    model = order_models.Order
    template_name = "app_settings/order/orders_list.html"
    context_object_name = "orders"
    queryset = order_services.AdminOrderHAndler.get_all_order()
    extra_context = {"status_list": order_models.Order.STATUS}

    def get(self, request, status=None, **kwargs):
        """GET-функция для рендеренга списка заказов."""
        super().get(request, **kwargs)
        object_list = self.get_queryset()
        if self.request.GET:
            # STATUS
            if self.request.GET.get("status"):
                status = self.request.GET.getlist("status")
                object_list = object_list.filter(status__in=status)
            # SEARCH
            if self.request.GET.get("search"):
                search = self.request.GET.get("search")
                object_list = object_list.filter(id=search)

        context = {
            "orders": object_list,
            "status_list": order_models.Order.STATUS,
        }
        return render(request, self.template_name, context=context)


class OrderDetailView(AdminOnlyMixin, generic.DetailView):
    """Класс-представление для отображения одного заказа."""

    model = order_models.Order
    template_name = "app_settings/order/order_detail.html"
    context_object_name = "order"
    STATUS_LIST_ORDER = order_models.Order().STATUS

    def get(self, request, *args, category=None, **kwargs):
        """GET-функция для рендеренга одного заказа."""
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        order = self.get_object()
        context["items"] = order.order_items.all()
        context["total"] = (
            context["items"].aggregate(
                total_cost=Sum("total")).get("total_cost")
        )
        context["status_list"] = self.STATUS_LIST_ORDER
        return self.render_to_response(context)
