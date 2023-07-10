from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
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
from app_store import forms as store_forms
# services
from app_item.services import comment_services
from app_order.services import order_services
from app_item.services import item_services
# other
from utils.my_utils import AdminOnlyMixin, MixinPaginator


class AdminDashBoardView(AdminOnlyMixin, generic.TemplateView):
    template_name = 'app_settings/admin/dashboard.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['comments'] = comment_services.CommentHandler.total_comments()
        context['orders'] = order_services.AdminOrderHAndler.orders().count()
        context['customer'] = auth_modals.Profile.objects.filter(user__groups__name='customer').count()
        context['seller'] = auth_modals.Profile.objects.filter(user__groups__name='seller').count()
        context['stores'] = store_modals.Store.objects.filter(is_active=True).count()
        context['items'] = item_models.Item.objects.filter(is_active=False).count()
        context['comments'] = item_models.Comment.objects.filter(is_published=False).count()
        context['categories'] = item_models.Category.objects.count()
        context['tags'] = item_models.Tag.objects.count()
        return self.render_to_response(context)


class SettingsView(AdminOnlyMixin,generic.TemplateView):
    template_name = 'app_settings/admin/settings.html'


class SettingsUpdatedView(AdminOnlyMixin, generic.UpdateView):
    model = settings_modals.SiteSettings
    template_name = 'app_settings/admin/settings_edit.html'
    form_class = admin_forms.UpdateSettingsForm
    MESSAGE_SUCCESS = "Настройки обновлены"
    MESSAGE_ERROR = "Ошибка. Настройки не обновлены."

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.SUCCESS, self.MESSAGE_SUCCESS)
        return redirect('app_settings:dashboard')

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, self.MESSAGE_ERROR)
        return super().form_invalid(form)


class CustomerListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списка покупателей."""
    model = auth_modals.User
    template_name = 'app_settings/customer/customer_list.html'
    paginate_by = 4

    def get_queryset(self):
        queryset = auth_modals.User.objects.filter(groups__name='customer').annotate(amount=Count('user_order')).order_by('-amount')
        return queryset

    def get(self, request, *args, **kwargs):
        object_list = self.get_queryset()
        if self.request.GET:
            if self.request.GET.get('search'):
                search = str(self.request.GET.get('search')).title()
                object_list = object_list.filter(
                    Q(first_name__startswith=search) |
                    Q(last_name__startswith=search)
                )
        object_list = MixinPaginator(object_list, self.request, self.paginate_by).my_paginator()
        return render(self.request, self.template_name, {'object_list': object_list})


class CustomerDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для блокировки/разблокировки покупатель."""
    model = auth_modals.User

    def get(self, request, *args, **kwargs):
        customer_id = kwargs['pk']
        try:
            customer = auth_modals.User.objects.get(id=customer_id)
            if customer.profile.is_active:
                customer.profile.is_active = False
                message = f"Покупатель {customer.get_full_name()} разблокирован"
            else:
                customer.profile.is_active = True
                message = f"Покупатель {customer.get_full_name()} заблокирован"
            customer.profile.save()
            messages.add_message(self.request, messages.WARNING, message)
            return redirect('app_settings:customer_list')
        except ObjectDoesNotExist:
            raise Http404("Такого покупателя не существует не существует")


class SellerListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списока продавцов."""
    model = auth_modals.User
    template_name = 'app_settings/seller/seller_list.html'
    paginate_by = 4

    def get_queryset(self):
        queryset = auth_modals.User.objects.filter(groups__name='seller')
        return queryset

    def get(self, request, *args, **kwargs):
        object_list = self.get_queryset()
        if self.request.GET:
            if self.request.GET.get('search'):
                search = self.request.GET.get('search')
                object_list = object_list.filter(
                    Q(first_name__startswith=search) |
                    Q(last_name__startswith=search)
                )
        object_list = MixinPaginator(object_list, self.request, self.paginate_by).my_paginator()
        return render(self.request, self.template_name, {'object_list': object_list})


class SellerDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для блокировки/разблокировки продавеца."""
    model = auth_modals.User

    def get(self, request, *args, **kwargs):
        seller_id = kwargs['pk']
        try:
            seller = auth_modals.User.objects.get(id=seller_id)
            if seller.profile.is_active:
                seller.profile.is_active = False
                message = f"Продавец {seller.get_full_name()} заблокирован"
            else:
                seller.profile.is_active = True
                message = f"Продавец {seller.get_full_name()} разблокирован "
            seller.profile.save()
            messages.add_message(self.request, messages.WARNING, message)
            return redirect('app_settings:seller_list')
        except ObjectDoesNotExist:
            raise Http404("Такого продавец не существует не существует")


class StoreListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списка магазинов."""
    model = store_modals.Store
    template_name = 'app_settings/store/store_list.html'
    paginate_by = 4
    queryset = store_modals.Store.objects.order_by('created')

    def get(self, request, *args, **kwargs):
        object_list = self.queryset
        if self.request.GET:
            if self.request.GET.get('search'):
                search = self.request.GET.get('search')
                object_list = object_list.filter(
                    Q(title__startswith=search) |
                    Q(owner__first_name__startswith=search)
                )
        object_list = MixinPaginator(object_list, self.request, self.paginate_by).my_paginator()
        return render(self.request, self.template_name, {'object_list': object_list})


class ProductListView(AdminOnlyMixin, generic.ListView):
    """Класс-представление для списка товаров."""
    model = item_models.Item
    template_name = 'app_settings/item/item_list.html'
    paginate_by = 4
    queryset = item_models.Item.objects.order_by('created')

    def get(self, request, *args, **kwargs):
        object_list = self.queryset
        if self.request.GET:
            if self.request.GET.get('search'):
                search = self.request.GET.get('search')
                object_list = object_list.filter(
                    Q(title__startswith=search) |
                    Q(id=search)
                )
        object_list = MixinPaginator(object_list, self.request, self.paginate_by).my_paginator()
        return render(self.request, self.template_name, {'object_list': object_list})


class CategoryListView(AdminOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех категорий товаров."""
    model = item_models.Category
    template_name = 'app_settings/category/category_list.html'
    paginate_by = 5

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        GET-функция возвращает все категории товаров
        или определенную категорию товаров, если передан параметр ['sort_by_letter'],
        так же возвращает отфильтрованный(по существующим категориям) список всех букв алфавита
        для быстрого поиска категорий по алфавиту.
        :param request: HttpRequest
        :param kwargs:  ['sort_by_letter'] параметр фильтрации категорий
        :return: HttpResponse
        """
        alphabet_list = item_services.ItemHandler.get_alphabet_list()
        sort_by_letter = request.GET.get('sort_by_letter')
        category_title = request.GET.get('title')
        if sort_by_letter:
            categories = item_models.Category.objects.filter(title__istartswith=sort_by_letter)
        elif category_title:
            categories = item_models.Category.objects.filter(
                Q(title__icontains=category_title) |
                Q(title__istartswith=category_title)
            )
        else:
            categories = item_models.Category.objects.all()
        object_list = MixinPaginator(
            categories,
            self.request,
            self.paginate_by
        ).my_paginator()
        context = {
            'object_list': object_list,
            'alphabet': alphabet_list,
        }
        return render(request, self.template_name, context)


class CategoryCreateView(AdminOnlyMixin, generic.CreateView):
    """ Класс-представление для создания категории товаров."""
    model = item_models.Category
    template_name = 'app_settings/category/category_create.html'
    form_class = admin_forms.CreateCategoryForm
    extra_context = {'categories': item_models.Category.objects.filter(parent_category=None)}

    def form_valid(self, form):
        form.save()
        category_title = form.cleaned_data.get('title')
        messages.add_message(self.request, messages.SUCCESS, f'Категория - "{category_title}" создана')
        return redirect('app_settings:category_list')



class CategoryUpdateView(AdminOnlyMixin, generic.UpdateView):
    """ Класс-представление для обновления категории товаров."""
    model = item_models.Category
    template_name = 'app_settings/category/category_edit.html'
    form_class = admin_forms.UpdateCategoryForm

    def form_valid(self, form):
        form.save()
        category_title = form.cleaned_data.get('title')
        messages.add_message(self.request, messages.SUCCESS, f'Категория - "{category_title}" обновлена')
        return redirect('app_settings:category_list')

    def form_invalid(self, form):
        return super(CategoryUpdateView, self).form_invalid(form)


class CategoryDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для удаления категории."""
    model = item_models.Category

    def get(self, request, *args, **kwargs):
        category = kwargs['pk']
        try:
            category = item_models.Category.objects.get(id=category)
            if category.is_archived:
                category.is_archived = False
                message = f"Категория {category} возращена из  архива"
            else:
                category.is_archived = True
                message = f"Категория {category} успешно удалена в архив"
            category.save()
            messages.add_message(self.request, messages.WARNING, message)
            return redirect('app_settings:category_list')
        except ObjectDoesNotExist:
            raise Http404("Такой категории не существует")


class TagListView(AdminOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех тегов товаров."""
    model = item_models.Tag
    template_name = 'app_settings/tag/tag_list.html'
    paginate_by = 5
    queryset = item_models.Tag.all_objects.all()

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        object_list = self.get_queryset()
        if self.request.GET:
            if self.request.GET.get('search'):
                search = self.request.GET.get('search')
                object_list = object_list.filter(title__startswith=search)
        object_list = MixinPaginator(object_list, self.request, self.paginate_by).my_paginator()
        context = {'object_list': object_list}
        return render(request, self.template_name, context)


class TagCreateView(AdminOnlyMixin, generic.CreateView):
    """Класс-представление для создания тега."""
    model = item_models.Category
    template_name = 'app_settings/tag/tag_edit.html'
    form_class = store_forms.CreateTagForm

    def form_valid(self, form):
        form.save()
        tag_title = form.cleaned_data.get('title').lower()
        messages.add_message(self.request, messages.SUCCESS, f'Тег - "{tag_title}" создан')
        return redirect('app_settings:tag_list')

    def form_invalid(self, form):
        form = store_forms.CreateTagForm(self.request.POST)
        return super(TagCreateView, self).form_invalid(form)


class TagUpdateView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для обновления тега."""
    model = item_models.Tag
    template_name = 'app_settings/tag/tag_edit.html'
    form_class = store_forms.CreateTagForm

    def form_valid(self, form):
        form.save()
        tag_title = form.cleaned_data.get('title').upper()
        messages.add_message(self.request, messages.SUCCESS, f'Тег - "{tag_title}" изменен')
        return redirect('app_settings:tag_list')

    def form_invalid(self, form):
        form = store_forms.CreateTagForm(self.request.POST)
        return super(TagUpdateView, self).form_invalid(form)


class TagDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для удаления тега."""
    model = item_models.Tag

    def get(self, request, *args, **kwargs):
        tag_id = kwargs['pk']
        try:
            tag = item_models.Tag.all_objects.get(id=tag_id)
            if tag.is_active:
                tag.is_active = False
                message = f"Тег - '{tag}' не активен"
            else:
                tag.is_active = True
                message = f"Характеристика - '{tag}' снова активен"
            tag.save()
            messages.add_message(self.request, messages.WARNING, message)
            return redirect('app_settings:tag_list')
        except ObjectDoesNotExist:
            raise Http404("Такой характеристики не существует")


class FeatureListView(AdminOnlyMixin, generic.DetailView):
    """Класс-представление для отображения списка всех характеристик категории."""
    model = item_models.Category
    template_name = 'app_settings/feature/feature_list.html'

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        super(FeatureListView, self).get(request, *args, **kwargs)
        category = self.get_object()
        features = item_models.Feature.all_objects.prefetch_related('categories').filter(categories=category)
        values = item_models.FeatureValue.all_objects.select_related('feature').filter(feature__in=features)
        context = {'features': features, 'category': category, 'values': values}
        return render(request, self.template_name, context)


class FeatureCreateView(AdminOnlyMixin, generic.CreateView):
    """Класс-представление для создания характеристики  категории."""
    model = item_models.Feature
    template_name = 'app_settings/feature/feature_create.html'
    form_class = store_forms.CreateFeatureForm
    extra_context = {}

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        context = {'category': self.kwargs['pk']}
        return render(self.request, self.template_name, context)

    def form_valid(self, form):
        feature = form.save()
        category_id = self.kwargs.get('pk')
        category = item_models.Category.objects.get(id=category_id)
        feature.categories.add(category.id)
        messages.add_message(self.request, messages.SUCCESS, f'Характеристика - "{feature}" добавлено')
        return redirect('app_settings:feature_list', category_id)

    def form_invalid(self, form):
        form = store_forms.CreateFeatureForm(self.request.POST)
        messages.add_message(self.request, messages.ERROR, f'Произошла ошибка - {form.errors}')
        category_id = self.kwargs.get('pk')
        return redirect('app_settings:feature_create', category_id)


class FeatureUpdateView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для обновления характеристики категории."""
    model = item_models.Feature
    template_name = 'app_settings/feature/feature_edit.html'
    form_class = admin_forms.UpdateFeatureForm

    def form_valid(self, form):
        form.save()
        category_id = self.kwargs['category_id']
        feature_title = form.cleaned_data.get('title')
        messages.add_message(self.request, messages.SUCCESS, f'Характеристика - "{feature_title}" обновлена')
        return redirect('app_settings:feature_list', category_id)

    def form_invalid(self, form):
        form = store_forms.CreateCategoryForm(self.request.POST)
        return super(FeatureUpdateView, self).form_invalid(form)


class FeatureDeleteView(AdminOnlyMixin, generic.UpdateView):
    """ Класс-представление для удаления характеристики категории."""
    model = item_models.Feature

    def get(self, request, *args, **kwargs):
        feature_id = kwargs['pk']
        category_id = kwargs['category_id']
        try:
            feature = item_models.Feature.all_objects.get(id=feature_id)
            if feature.is_active:
                feature.is_active = False
                message = f"Характеристика - '{feature}' не активна"
            else:
                feature.is_active = True
                message = f"Характеристика - '{feature}' снова активна"
            feature.save()
            messages.add_message(self.request, messages.WARNING, message)
            return redirect('app_settings:feature_list', category_id)
        except ObjectDoesNotExist:
            raise Http404("Такой характеристики не существует")


class ValueCreateView(AdminOnlyMixin, generic.CreateView):
    """ Класс-представление для создания значения характеристики."""
    model = item_models.FeatureValue
    template_name = 'app_settings/feature/value_create.html'
    form_class = store_forms.CreateValueForm

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        category_id = item_models.Category.objects.get(feature=self.kwargs['pk']).id
        context = {'category_id': category_id}
        return render(self.request, self.template_name, context)

    def form_valid(self, form):
        value = form.save(commit=False)
        feature_id = self.kwargs.get('pk')
        feature = item_models.Feature.objects.get(id=feature_id)
        value.feature = feature
        value.save()
        category = item_models.Category.objects.get(feature=feature)
        print(category.id)

        messages.add_message(self.request, messages.SUCCESS, f'Значение - "{value}" добавлено')
        return redirect('app_settings:feature_list', category.id)

    def form_invalid(self, form):
        form = store_forms.CreateValueForm(self.request.POST)
        feature_id = self.kwargs.get('pk')
        feature = item_models.Feature.objects.get(id=feature_id)
        messages.add_message(self.request, messages.ERROR, f"{form.errors.get('value')}")
        return redirect('app_settings:value_create', feature.pk )


class ValueDeleteView(AdminOnlyMixin, generic.UpdateView):
    """ Класс-представление для удаления значение характеристики категории."""
    model = item_models.FeatureValue

    def get(self, request, *args, **kwargs):
        value_id = kwargs['pk']
        category_id = kwargs['category_id']
        try:
            value = item_models.FeatureValue.all_objects.get(id=value_id)
            if value.is_active:
                value.is_active = False
                message = f"Характеристика - '{value}' не активна"
            else:
                value.is_active = True
                message = f"Характеристика - '{value}' снова активна"
            value.save()
            messages.add_message(self.request, messages.WARNING, message)
            return redirect('app_settings:feature_list', category_id)
        except ObjectDoesNotExist:
            raise Http404("Такой характеристики не существует")


class CommentListView(AdminOnlyMixin, generic.ListView, MixinPaginator):
    """ Класс-представление для отображения списка всех комментариев."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_list.html'
    paginate_by = 4

    def get(self, request, *args, **kwargs):
        object_list = item_models.Comment.objects.all()
        if request.GET:
            if request.GET.get('new'):
                object_list = object_list.filter(is_published=False)
            elif request.GET.get('moderated'):
                object_list = object_list.filter(Q(is_published=True) & Q(archived=False))
            elif request.GET.get('archived'):
                object_list = object_list.filter(archived=True)
        object_list = MixinPaginator(
            request=request,
            object_list=object_list,
            per_page=self.paginate_by
        ).my_paginator()
        context = {'object_list': object_list}
        return render(request, self.template_name, context=context)


class CommentDetail(AdminOnlyMixin, generic.DetailView):
    """ Класс-представление для отображения одного комментария."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_detail.html'
    context_object_name = 'comment'


class CommentDelete(AdminOnlyMixin, generic.DeleteView):
    """ Класс-представление для удаления комментария."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_delete.html'
    MESSAGE = 'момментарий удален'

    def form_valid(self, form):
        self.object.archived = True
        self.object.save()
        messages.add_message(self.request, messages.WARNING, self.MESSAGE)
        return HttpResponseRedirect(self.object.get_absolute_url())


class CommentModerate(AdminOnlyMixin, generic.UpdateView):
    """ Класс-представление для изменения статуса комментария(прохождение модерации)."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_update.html'
    fields = ['is_published']
    success_url = reverse_lazy('app_settings:comments_list')


class OrderListView(generic.ListView):
    """ Класс-представление для отображения списка всех заказов."""
    model = order_models.Order
    template_name = 'app_settings/order/orders_list.html'
    context_object_name = 'orders'
    queryset = order_models.Order.objects.all()
    extra_context = {'status_list': order_models.Order.STATUS}

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        object_list = self.get_queryset()
        if self.request.GET:
            # STATUS
            if self.request.GET.get('status'):
                status = self.request.GET.getlist('status')
                object_list = object_list.filter(status__in=status)
            # SEARCH
            if self.request.GET.get('search'):
                search = self.request.GET.get('search')
                object_list = object_list.filter(id=search)

        context = {
            'orders': object_list,
            'status_list': order_models.Order.STATUS,
        }
        return render(request, self.template_name, context=context)


class OrderDetailView(AdminOnlyMixin, generic.DetailView):
    """ Класс-представление для отображения одного заказа."""
    model = order_models.Order
    template_name = 'app_settings/order/order_detail.html'
    context_object_name = 'order'
    STATUS_LIST_ORDER = order_models.Order().STATUS

    def get(self, request, *args, category=None, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        order = self.get_object()
        context['items'] = order.order_items.all()
        context['total'] = context['items'].aggregate(total_cost=Sum('total')).get('total_cost')
        context['status_list'] = self.STATUS_LIST_ORDER
        return self.render_to_response(context)


