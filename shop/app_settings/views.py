from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Count, Q
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse, Http404
from django.shortcuts import redirect
from django.shortcuts import render
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
        return self.render_to_response(context)


class SettingsView(AdminOnlyMixin,generic.TemplateView):
    template_name = 'app_settings/admin/settings.html'


class SettingsUpdatedView(AdminOnlyMixin, generic.UpdateView):
    model = settings_modals.SiteSettings
    template_name = 'app_settings/admin/settings_edit.html'
    form_class = admin_forms.UpdateSettingsForm
    
    def form_valid(self, form):
        super(SettingsUpdatedView, self).form_valid(form)
        form.save()
        return redirect('app_settings:dashboard')

    def form_invalid(self, form):
        super(SettingsUpdatedView).form_invalid(form)
        return redirect('app_settings:settings_edit', pk=1)


class CustomerListView(AdminOnlyMixin, generic.ListView):
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
    """Класс-представление для блокировки/разблокировки продавец."""
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
        alphabet_list = sorted(set([category.title[0] for category in item_models.Category.objects.order_by('title')]))
        sort_by_letter = request.GET.get('sort_by_letter')
        if sort_by_letter:
            categories = item_models.Category.objects.filter(title__istartswith=sort_by_letter)
        else:
            categories = item_models.Category.objects.all()
        categories = MixinPaginator(categories, self.request, self.paginate_by).my_paginator()
        context = {
            'object_list': categories,
            'alphabet': alphabet_list
        }
        return render(request, self.template_name, context)


class CategoryCreateView(AdminOnlyMixin, generic.CreateView):
    """Класс-представление для создания категории товаров."""
    model = item_models.Category
    template_name = 'app_settings/category/category_list.html'
    form_class = admin_forms.CreateCategoryForm

    def form_valid(self, form):
        form.save()
        category_title = form.cleaned_data.get('title')
        messages.add_message(self.request, messages.SUCCESS, f'Категория - "{category_title}" создана')
        return redirect('app_store:category_list')

    def form_invalid(self, form):
        form = store_forms.CreateCategoryForm(self.request.POST)
        return super(CategoryCreateView, self).form_invalid(form)


class CategoryUpdateView(AdminOnlyMixin, generic.UpdateView):
    model = item_models.Category
    template_name = 'app_settings/category/category_edit.html'
    form_class = admin_forms.UpdateCategoryForm

    def form_valid(self, form):
        form.save()
        category_title = form.cleaned_data.get('title')
        messages.add_message(self.request, messages.SUCCESS, f'Категория - "{category_title}" обновлена')
        return redirect('app_settings:category_list')

    def form_invalid(self, form):
        form = store_forms.CreateCategoryForm(self.request.POST)
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
    queryset = item_models.Tag.objects.all()

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
    """Класс-представление для создания категории товаров."""
    model = item_models.Category
    template_name = 'app_settings/tag/tag_edit.html'
    form_class = store_forms.CreateTagForm

    def form_valid(self, form):
        form.save()
        tag_title = form.cleaned_data.get('title').upper()
        messages.add_message(self.request, messages.SUCCESS, f'Тег - "{tag_title}" создан')
        return redirect('app_settings:tag_list')

    def form_invalid(self, form):
        form = store_forms.CreateTagForm(self.request.POST)
        return super(TagCreateView, self).form_invalid(form)


class TagUpdateView(AdminOnlyMixin, generic.UpdateView):
    model = item_models.Category
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


class FeatureListView(AdminOnlyMixin, generic.DetailView):
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
    """Класс-представление для создания характеристики  товаров."""
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
        print(form.errors)
        return super(FeatureUpdateView, self).form_invalid(form)


class FeatureDeleteView(AdminOnlyMixin, generic.UpdateView):
    """Класс-представление для удаления характеристики товара."""
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
    """Класс-представление для создания значения характеристики  товаров."""
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
        messages.add_message(self.request, messages.SUCCESS, f'Значение - "{value}" добавлено')
        return redirect('app_settings:feature_list', category.id)

    def form_invalid(self, form):
        super(ValueCreateView, self).form_invalid(form)
        form = store_forms.CreateValueForm(self.request.POST)
        feature_id = self.kwargs.get('pk')
        feature = item_models.Feature.objects.get(id=feature_id)
        category = item_models.Category.objects.get(feature=feature)
        messages.add_message(self.request, messages.ERROR, f'{form.errors}')
        return redirect('app_store:feature_list', category.slug)


class ValueDeleteView(AdminOnlyMixin, generic.UpdateView):
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


class CommentListView(generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех заказов продавца."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 5


class CommentDetail(generic.DetailView):
    """Класс-представление для отображения одного комментария."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_detail.html'
    context_object_name = 'comment'


class CommentDelete(generic.DeleteView):
    """Класс-представление для удаления комментария."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_delete.html'

    def form_valid(self, form):
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())


class CommentModerate(generic.UpdateView):
    """Класс-представление для изменения статуса комментария(прохождение модерации)."""
    model = item_models.Comment
    template_name = 'app_settings/comment/comment_update.html'
    fields = ['is_published']


class OrderListView(generic.ListView):
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
    """Класс-представление для отображения одного заказа в магазине продавца."""
    model = order_models.Order
    template_name = 'app_settings/order/admin_order_detail.html'
    context_object_name = 'order'

    def get(self, request, *args, category=None, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        stores = request.user.store.all()
        order = self.get_object()
        context['items'] = order.order_items.filter(item__item__store__in=stores)
        context['total'] = context['items'].aggregate(total_cost=Sum('total')).get('total_cost')
        return self.render_to_response(context)


