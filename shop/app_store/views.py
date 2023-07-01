import csv
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.db.models import Sum, Q
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic
from django.http import HttpResponse

# models
from app_item import models as item_models
from app_order import models as order_models
from app_store import models as store_models

# services
from app_item.services import comment_services
from app_order.services import order_services
from app_item.services import item_services
from app_store.services import store_services

# forms
from app_order import forms as order_form
from app_store import forms as store_forms

# other
from utils.my_utils import MixinPaginator, SellerOnlyMixin
from app_order import tasks


class SellerDashBoardView(SellerOnlyMixin, generic.TemplateView):
    template_name = 'app_store/dashboard.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['comments'] = comment_services.CommentHandler.seller_stores_comments(request)
        context['orders'] = order_services.SellerOrderHAndler.get_seller_order_list(request.user.id).count()
        context['stores'] = store_services.StoreHandler.get_all_story_by_owner(request.user).count()

        return self.render_to_response(context)


# STORE VIEWS #
class StoreListView(SellerOnlyMixin, generic.ListView):
    """Класс-представление для отображения списка всех магазинов продавца."""
    model = store_models.Store
    template_name = 'app_store/store/store_list.html'
    context_object_name = 'stores'

    def queryset(self):
        owner = self.request.user
        queryset = store_services.StoreHandler.get_all_story_by_owner(owner)
        return queryset


class StoreDetailView(UserPassesTestMixin, generic.DetailView, MixinPaginator):
    """Класс-представление для отображения одного магазина."""
    model = store_models.Store
    template_name = 'app_store/store/store_detail.html'
    context_object_name = 'store'
    paginate_by = 7

    def test_func(self):
        user = self.request.user
        store = self.get_object()
        return True if user == store.owner else False

    def get(self, request, *args, category=None, **kwargs):
        """
        Функция возвращает экземпляр магазина,
        object_list - список товаров этого магазина,
        categories - категории товаров,
        total_profit - сумма всех проданных  товаров,
        message- сообщение о параметрах сортировки
        :param request: request
        :param category: категория товара
        :param kwargs: 'order_by' параметр сортировки товаров
        :return: response
        """
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        store = self.get_object()
        all_items = store.items.all()

        try:
            category_slug = kwargs['slug']
            category = item_services.CategoryHandler.get_categories(category_slug)
            items = all_items.filter(category=category)
        except (ObjectDoesNotExist, KeyError):
            items = all_items
        if request.GET.get('q'):
            query = str(request.GET.get('q'))  # [:-1]
            title = query.title()
            lower = query.lower()
            items = all_items.select_related('category', 'store'). \
                prefetch_related('tag', 'views', 'images', 'feature_value'). \
                filter(
                Q(title__icontains=title) |
                Q(title__icontains=lower)
            ).distinct()
        if request.GET.get('order_by', None):
            order_by = request.GET.get('order_by')
            items = store_services.StoreHandler.ordering_store_items(queryset=items, order_by=order_by)
            context['message'] = store_services.StoreHandler.ordering_message(order_by=order_by)

        context['categories'] = item_services.CategoryHandler.get_categories_in_items_set(all_items)
        context['object_list'] = MixinPaginator(items, self.request, self.paginate_by).my_paginator()
        context['total_profit'] = store_services.StoreHandler.total_profit_store(store)

        return self.render_to_response(context)


class StoreCreateView(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания магазина."""
    model = store_models.Store
    template_name = 'app_store/store/create_store.html'
    form_class = store_forms.CreateStoreForm

    def form_valid(self, form):
        store = form.save()
        store.is_active = True
        store.owner = self.request.user
        store.save()
        return redirect('app_store:store_detail', store.pk)

    def form_invalid(self, form):

        form = store_forms.CreateStoreForm(self.request.POST, self.request.FILES)
        messages.add_message(self.request, messages.ERROR, f"Ошибка. Магазин не создан. Повторите попытку.")
        return super().form_invalid(form)


class StoreUpdateViews(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для обновления магазина."""
    model = store_models.Store
    template_name = 'app_store/store/store_edit.html'
    context_object_name = 'store'
    form_class = store_forms.UpdateStoreForm
    message = 'Данные магазтина обновлены'

    def test_func(self):
        user = self.request.user
        store = self.get_object()
        return True if user == store.owner else False

    def get_success_url(self):
        store = self.get_object()
        return redirect('app_store:store_edit', store.pk)

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.SUCCESS, self.message)
        return self.get_success_url()

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, self.message)
        return super(StoreUpdateViews, self).form_invalid(form)


# ITEM VIEWS #
class ItemCreateView(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания и добавления товара в магазин."""
    model = store_models.Store
    template_name = 'app_store/item/add_item.html'
    form_class = store_forms.AddItemImageForm
    second_form_class = store_forms.TagFormSet

    def get_context_data(self, **kwargs):
        formset_tag = store_forms.TagFormSet(queryset=item_models.Tag.objects.none())
        formset_image = store_forms.ImageFormSet(queryset=item_models.Image.objects.none())
        context = {
            'tag_formset': formset_tag,
            'image_formset': formset_image,
            'form': self.form_class,
            'store': self.get_object(),
            'colors': item_services.get_colors(item_models.Item.available_items.all())
        }
        return context

    def form_valid(self, form):
        with transaction.atomic():
            item = form.save(commit=False)
            item.is_active = True
            item.save()
            tag_list = form.cleaned_data.get('tag')
            for t in tag_list:
                tag = item_models.Tag.objects.get(id=t.id)
                item.tag.add(tag)
                item.save()
            if len(self.request.FILES.getlist('image')) == 1:
                img = self.request.FILES.getlist('image')[0]
                image = item_models.Image.objects.create(image=img, title=item.title)
                item.images.add(image.id)
                item.save()
            else:
                for img in self.request.FILES.getlist('image'):
                    image = item_models.Image.objects.create(image=img, title=item.title)
                    item.images.add(image.id)
                    item.save()
            store_id = self.kwargs['pk']
            store = store_services.StoreHandler.get_store(store_id)
            store.items.add(item)
            store.save()
            messages.add_message(self.request, messages.SUCCESS, f"Товаре {item} добавлен")
        return redirect('app_store:store_detail', store.pk)

    def form_invalid(self, form):
        form = store_forms.AddItemImageForm(self.request.POST, self.request.FILES)
        messages.add_message(self.request, messages.ERROR, f"Ошибка. Товар не создан. Повторите попытку.")
        return super().form_invalid(form)


class ItemUpdateView(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для обновления товара."""
    model = item_models.Item
    template_name = 'app_store/item/edit_item.html'
    form_class = store_forms.UpdateItemForm
    second_form_class = store_forms.UpdateItemImageForm
    # extra_context = {'colors': item_services.get_colors(item_models.Item.available_items.all()),
    #                  'image_formset': store_forms.ImageFormSet(queryset=item_models.Image.objects.none())}

    def test_func(self):
        user = self.request.user
        item = self.get_object()
        return True if user == item.store.owner else False

    def get(self, *args, **kwargs):
        formset_tag = store_forms.TagFormSet(queryset=item_models.Tag.objects.none())
        formset_image = store_forms.ImageFormSet(queryset=item_models.Image.objects.none())
        context = {
            'tag_formset': formset_tag,
            'image_formset': formset_image,
            'form': self.form_class,
            'colors': item_services.get_colors(item_models.Item.objects.all()),
            'item': self.get_object(),
        }
        return self.render_to_response(context=context)

    def form_valid(self, form):
        instance = self.get_object()
        form = store_forms.UpdateItemForm(
            data=self.request.POST,
            instance=self.get_object(),
        )
        form.save()
        # if form.has_changed():
        #     fields_for_update = []
        #     for field in form.changed_data:
        #         if form.data[field] != '' and form.data[field]:
        #             fields_for_update.append(field)
        #             instance.field = form.data[field]
        #             instance.__setattr__(field, form.data[field])
        # instance.save(update_fields=[*fields_for_update])

        for new_value in self.request.POST.getlist('value'):
            if new_value:
                feature = item_models.Feature.objects.filter(values=new_value).first()
                if feature:
                    if instance.feature_value.all():
                        for old_value in instance.feature_value.all():
                            if old_value.feature == feature:
                                instance.feature_value.remove(old_value)
                    instance.feature_value.add(new_value)
                    instance.save()

        for i in self.request.FILES.getlist('image'):
            img = item_models.Image.objects.create(image=i, title=instance.title)
            if img not in instance.images.all():
                instance.images.add(img)
                instance.save()

        messages.add_message(self.request, messages.SUCCESS, f"Данные о товаре {instance} обновлены")
        return super().form_invalid(form)

    def form_invalid(self, form):
        form = store_forms.UpdateItemImageForm(self.request.POST, self.request.FILES)
        # messages.add_message(self.request, messages.ERROR, f"Ошибка.")
        return super().form_invalid(form)

    def get_success_url(self):
        item = self.get_object()
        store_id = item.store.id
        return reverse('app_store:store_detail', kwargs={'pk': store_id})


class ItemDeleteView(UserPassesTestMixin, generic.DeleteView):
    """Класс-представление для удаления товара."""
    model = item_models.Item

    def test_func(self):
        user = self.request.user
        item = self.get_object()
        return True if user == item.store.owner else False

    def get(self, request, *args, **kwargs):
        item_id = kwargs['item_id']
        user = self.request.user
        try:
            item = item_models.Item.objects.get(id=item_id)
            item.is_active = True
            item.save()
            messages.add_message(self.request, messages.ERROR, f"Товар {item} успешно удален")
            return redirect('app_user:account', user.pk)
        except ObjectDoesNotExist:
            raise Http404("Такой товар не существует")


# CATEGORY VIEW #


# class CategoryListView(SellerOnlyMixin, generic.DetailView, MixinPaginator):
#     """Класс-представление для отображения списка всех категорий товаров."""
#     model = item_models.Store
#     template_name = 'app_store/category/category_list.html'
#     paginate_by = 5
#
#     def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
#         """
#         GET-функция возвращает все категории товаров
#         или определенную категорию товаров, если передан параметр ['sort_by_letter'],
#         так же возвращает отфильтрованный(по существующим категориям) список всех букв алфавита
#         для быстрого поиска категорий по алфавиту.
#         :param request: HttpRequest
#         :param kwargs:  ['sort_by_letter'] параметр фильтрации категорий
#         :return: HttpResponse
#         """
#         alphabet_list = sorted(set([category.title[0] for category in item_models.Category.objects.order_by('title')]))
#         sort_by_letter = request.GET.get('sort_by_letter')
#         store = self.get_object()
#         if sort_by_letter:
#             categories = item_models.Category.objects.filter(title__istartswith=sort_by_letter)
#         else:
#             categories = item_models.Category.objects.all()
#         categories = MixinPaginator(categories, self.request, self.paginate_by).my_paginator()
#         context = {'object_list': categories, 'alphabet': alphabet_list, 'store': store}
#         return render(request, self.template_name, context)
#
#
# class CategoryCreateView(SellerOnlyMixin, generic.CreateView):
#     """Класс-представление для создания категории товаров."""
#     model = item_models.Category
#     template_name = 'app_store/category/category_list.html'
#     form_class = store_forms.CreateCategoryForm
#
#     def get(self, request, *args, **kwargs):
#         super().get(request, *args, **kwargs)
#         context = {'store': self.kwargs['pk']}
#         return render(self.request, self.template_name, context)
#
#     def form_valid(self, form):
#         form.save()
#         category_title = form.cleaned_data.get('title')
#         messages.add_message(self.request, messages.SUCCESS, f'Категория - "{category_title}" создана')
#         return redirect('app_store:category_list', self.kwargs['pk'])
#
#     def form_invalid(self, form):
#         form = store_forms.CreateCategoryForm(self.request.POST)
#         return super(CategoryCreateView, self).form_invalid(form)


# TAG VIEWS #
# class TagListView(SellerOnlyMixin, generic.ListView, MixinPaginator):
#     """Класс-представление для отображения списка всех тегов товаров."""
#     model = item_models.Tag
#     template_name = 'app_store/tag_list.html'
#     paginate_by = 20
#
#     def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
#
#         alphabet_list = sorted(set([tag.title[0] for tag in item_models.Tag.objects.order_by('title')]))
#         sort_by_letter = request.GET.get('sort_by_letter')
#         if sort_by_letter:
#             tag_set = item_models.Tag.objects.filter(title__istartswith=sort_by_letter)
#         else:
#             tag_set = item_models.Tag.objects.all()
#         object_list = MixinPaginator(tag_set, self.request, self.paginate_by).my_paginator()
#         context = {'object_list': object_list, 'alphabet': alphabet_list}
#         return render(request, self.template_name, context)
#
#
# class CreateTagView(SellerOnlyMixin, generic.CreateView):
#     """Класс-представление для создания категории товаров."""
#     model = item_models.Category
#     template_name = 'app_store/tag_list.html'
#     form_class = store_forms.CreateTagForm
#
#     def form_valid(self, form):
#         form.save()
#         tag_title = form.cleaned_data.get('title').upper()
#         messages.add_message(self.request, messages.SUCCESS, f'Тег - "{tag_title}" создан')
#         return redirect('app_store:tag_list')
#
#     def form_invalid(self, form):
#         form = store_forms.CreateTagForm(self.request.POST)
#         return super(CreateTagView, self).form_invalid(form)
#
#
# class AddTagToItem(SellerOnlyMixin, generic.UpdateView):
#     """Класс-представление для  добавления тега в карточку товара."""
#     model = item_models.Item
#     context_object_name = 'item'
#     template_name = 'app_store/add_tag.html'
#     form_class = store_forms.AddTagForm
#     MESSAGE = "Новый тег(и) успешно добавлен(ы)"
#
#     def form_valid(self, form):
#         tag_list = form.cleaned_data.get('tag')
#         item = item_models.Item.objects.get(id=self.kwargs['pk'])
#         for t in tag_list:
#             tag = item_models.Tag.objects.get(id=t.id)
#             item.tag.add(tag)
#             item.save()
#         messages.add_message(self.request, messages.INFO, self.MESSAGE)
#         return redirect('app_store:edit_item', item.pk)
#
#     def form_invalid(self, form):
#         messages.add_message(self.request, messages.ERROR, f"{form.errors}")
#         return self.render_to_response(self.get_context_data(form=form))
#
#
# class RemoveTagFromItem(generic.DeleteView):
#     """Класс-представление для удаления тега из карточки товара"""
#     model = item_models.Tag
#
#     def get(self, request, *args, **kwargs):
#         item_id = kwargs['item_id']
#         item = item_models.Item.objects.get(id=item_id)
#         tag_id = kwargs['tag_id']
#         tag = item_models.Tag.objects.get(id=tag_id)
#         if tag in item.tag.all():
#             item.tag.remove(tag)
#         item.save()
#         messages.add_message(self.request, messages.WARNING, f"Тег {tag} успешно удален")
#         return redirect('app_store:edit_item', item.pk)


# IMAGE VIEWS #
class DeleteImage(UserPassesTestMixin, generic.DeleteView):
    """Класс-представление для удаления изображения из карточки товара"""
    model = item_models.Image
    MESSAGE = "Изображение успешно удалено"

    def test_func(self):
        user = self.request.user
        image = self.get_object()
        owner = image.item_images.first().store.owner
        return True if user == owner else False

    def get(self, request, *args, **kwargs):
        image = self.get_object()
        item = image.item_images.first()
        if image in item.images.all():
            item.images.remove(image)
            item_models.Image.objects.filter(id=image.id).delete()
        item.save()
        messages.add_message(self.request, messages.WARNING, self.MESSAGE)
        return redirect('app_store:edit_item', item.pk)


class MakeImageAsMain(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для  выбора изображения как главного в карточке товара"""
    model = item_models.Image
    MESSAGE = "Изображение выбранно как гланое"

    def test_func(self):
        user = self.request.user
        image = self.get_object()
        owner = image.item_images.first().store.owner
        return True if user == owner else False

    def get(self, request, *args, **kwargs):
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
        return redirect('app_store:edit_item', item.pk)


# FEATURE VIEWS #
# class FeatureListView(SellerOnlyMixin, generic.DetailView):
#     model = item_models.Category
#     template_name = 'app_store/features/feature_list.html'
#
#     def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
#         super(FeatureListView, self).get(request, *args, **kwargs)
#         category = self.get_object()
#         features = item_models.Feature.objects.prefetch_related('categories').filter(categories=category)
#         values = item_models.FeatureValue.objects.select_related('feature').filter(feature__in=features)
#         context = {'features': features, 'category': category, 'values': values}
#         return render(request, self.template_name, context)
#
#
# class CreateFeatureView(SellerOnlyMixin, generic.CreateView):
#     """Класс-представление для создания характеристики  товаров."""
#     model = item_models.Feature
#     template_name = 'app_store/features/feature_create.html'
#     form_class = store_forms.CreateFeatureForm
#
#     def get(self, request, *args, **kwargs):
#         super().get(request, *args, **kwargs)
#         context = {'category': self.kwargs['pk']}
#         return render(self.request, self.template_name, context)
#
#     def form_valid(self, form):
#         feature = form.save()
#         category_id = self.kwargs.get('pk')
#         category = item_models.Category.objects.get(id=category_id)
#         feature.categories.add(category.id)
#         messages.add_message(self.request, messages.SUCCESS, f'Характеристика - "{feature}" добавлено')
#         return redirect('app_store:feature_list', category.slug)
#
#     def form_invalid(self, form):
#         form = store_forms.CreateFeatureForm(self.request.POST)
#         messages.add_message(self.request, messages.ERROR, f'Произошла ошибка - {form.errors}')
#         category_slug = self.kwargs.get('slug')
#         category = item_models.Category.objects.get(slug=category_slug)
#         return redirect('app_store:feature_create', category.slug)
#
#
# class CreateFeatureValueView(SellerOnlyMixin, generic.CreateView):
#     """Класс-представление для создания значения характеристики  товаров."""
#     model = item_models.FeatureValue
#     template_name = 'app_store/features/value_create.html'
#     form_class = store_forms.CreateValueForm
#
#     def get(self, request, *args, **kwargs):
#         super().get(request, *args, **kwargs)
#         category_id = item_models.Category.objects.get(feature=self.kwargs['pk']).id
#         context = {'category_id': category_id}
#         return render(self.request, self.template_name, context)
#
#     def form_valid(self, form):
#         value = form.save(commit=False)
#         feature_id = self.kwargs.get('feature_pk')
#         feature = item_models.Feature.objects.get(id=feature_id)
#         value.feature = feature
#         value.save()
#         category = item_models.Category.objects.get(feature=feature)
#         messages.add_message(self.request, messages.SUCCESS, f'Значение - "{value}" добавлено')
#         return redirect('app_store:feature_list', category.slug)
#
#     def form_invalid(self, form):
#         super(CreateFeatureValueView, self).form_invalid(form)
#         form = store_forms.CreateValueForm(self.request.POST)
#         feature_id = self.kwargs.get('feature_pk')
#         feature = item_models.Feature.objects.get(id=feature_id)
#         category = item_models.Category.objects.get(feature=feature)
#         messages.add_message(self.request, messages.ERROR, f'{form.errors}')
#         return redirect('app_store:feature_list', category.slug)
#
#
# class RemoveFeatureValueView(generic.DeleteView):
#     """Класс-представление для удаления изображения из карточки товара"""
#     model = item_models.Feature
#
#     # def test_func(self):UserPassesTestMixin
#     #     user = self.request.user
#     #     feature = self.get_object()
#     #     owner = feature.item_images.first().store.owner
#     #     return True if user == owner else False
#
#     def get(self, request, *args, **kwargs):
#
#         feature = item_models.Feature.objects.get(slug=self.kwargs.get('slug'))
#         values = feature.values.all()
#
#         # todo IN THE SERVICE start
#         item = item_models.Item.objects.get(id=self.kwargs.get('pk'))
#         for value in values:
#             if value in item.feature_value.all():
#                 item.feature_value.remove(value)
#                 item.save()
#         # IN THE SERVICE end (return ITEM)
#
#         messages.add_message(self.request, messages.INFO, f"Характеристика удалена")
#         return redirect('app_store:edit_item', item.pk)


# DELIVERY VIEWS #
class DeliveryListView(SellerOnlyMixin, generic.ListView):
    """Класс-представление для отображения списка всех заказов продавца."""
    model = order_models.Order
    template_name = 'app_store/delivery/delivery_list.html'
    context_object_name = 'orders'
    STATUS_LIST = order_models.Order().STATUS

    def get_queryset(self):
        stores = self.request.user.store.all()
        queryset = order_models.Order.objects.filter(store__in=stores).distinct().order_by('-created')
        return queryset

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        object_list = self.get_queryset()
        if self.request.GET:
            # STORE
            if self.request.GET.get('stores'):
                stores = self.request.GET.getlist('stores')
                object_list = self.get_queryset().filter(store__title__in=stores)
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
            'stores': request.user.store.all(),
            'status_list': self.STATUS_LIST
        }
        return render(request, self.template_name, context=context)


class DeliveryDetailView(UserPassesTestMixin, generic.DetailView):
    """Класс-представление для отображения одного заказа в магазине продавца."""
    model = order_models.Order
    template_name = 'app_store/delivery/delivery_detail.html'
    context_object_name = 'order'
    STATUS_LIST_ORDER = order_models.Order().STATUS
    STATUS_LIST_ITEM = order_models.OrderItem().STATUS

    def test_func(self):
        # user = self.request.user
        # order = self.get_object()
        return True  # if user == order.store.all()  else False

    def get(self, request, *args, category=None, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        stores = request.user.store.all()
        order = self.get_object()
        context['items'] = order.order_items.filter(item__item__store__in=stores)
        context['total'] = context['items'].aggregate(total_cost=Sum('total')).get('total_cost')
        context['status_list'] = self.STATUS_LIST_ORDER
        context['status_list_item'] = self.STATUS_LIST_ITEM
        return self.render_to_response(context)


class DeliveryUpdateView(UserPassesTestMixin, generic.UpdateView):
    model = order_models.Order
    template_name = 'app_store/delivery/delivery_edit.html'
    context_object_name = 'order'
    form_class = order_form.OrderItemUpdateForm

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.store.first().owner else False

    def form_valid(self, form):
        form.save()
        order = self.get_object()
        messages.add_message(self.request, messages.SUCCESS, f"Данные {order} успешно обновлены")
        return redirect('app_store:delivery_detail', order.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class OrderItemUpdateView(generic.UpdateView):
    """Класс-представление для обновления кол-во товаров в заказе."""
    model = order_models.OrderItem
    template_name = 'app_store/delivery/delivery_edit.html'
    form_class = order_form.OrderItemUpdateForm
    context_object_name = 'order_item'

    def form_valid(self, form):
        order_services.SellerOrderHAndler.update_item_in_order(self.request, form)
        messages.add_message(self.request, messages.SUCCESS, f"Количество товара({self.get_object()}) обновлено.")
        return redirect('app_store:order_item_edit', self.get_object().pk)

    def form_invalid(self, form):
        order_item = self.get_object()
        messages.add_message(self.request, messages.ERROR, f"Произошла ошибка при обновлении количества товара.")
        return redirect('app_store:order_item_edit', order_item.pk)


class SentPurchase(generic.UpdateView):
    """Класс-представление для отправки товара покупателю."""
    model = order_models.OrderItem
    template_name = 'app_store/delivery/delivery_detail.html'
    context_object_name = 'order'
    form_class = store_forms.UpdateOrderStatusForm

    def form_valid(self, form):
        super().form_invalid(form)
        form.save()
        status = form.cleaned_data['status']
        print('****************', status)
        order_item_id = self.kwargs['pk']
        order_item = order_services.SellerOrderHAndler.sent_item(order_item_id, status)
        tasks.check_order_status.delay(order_item.order.id)
        messages.add_message(self.request, messages.SUCCESS, f"{order_item} отправлен")
        return redirect(self.request.META.get('HTTP_REFERER'))

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, f"Произошла ошибка при отправки заказа.")
        return super().form_invalid(form)


class CommentListView(generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех заказов продавца."""
    model = item_models.Comment
    template_name = 'app_store/comments/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 5

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        object_list = order_services.SellerOrderHAndler.get_seller_comment_list(request)
        object_list = MixinPaginator(object_list, self.request, self.paginate_by).my_paginator()
        return render(request, self.template_name, {'object_list': object_list})


class CommentDetail(generic.DetailView):
    """Класс-представление для отображения одного комментария."""
    model = item_models.Comment
    template_name = 'app_store/comments/comment_detail.html'
    context_object_name = 'comment'


# class CommentDelete(generic.DeleteView):
#     """Класс-представление для удаления комментария."""
#     model = item_models.Comment
#     template_name = 'app_store/comment/comment_delete.html'
#
#     def form_valid(self, form):
#         self.object.archived = True
#         self.object.save()
#         return HttpResponseRedirect(self.object.get_absolute_url())
#
#
# class CommentModerate(generic.UpdateView):
#     """Класс-представление для изменения статуса комментария(прохождение модерации)."""
#     model = item_models.Comment
#     template_name = 'app_store/comment/comment_update.html'
#     fields = ['is_published']


class CommentList(generic.ListView):
    model = item_models.Comment
    template_name = 'app_store/comment/comment_list.html'

    def get(self, request, *args, **kwargs):
        comment_id = kwargs['pk']
        action = kwargs['slug']
        if action == 'approve':
            comment_services.CommentHandler.set_comment_approved(comment_id)
            messages.add_message(self.request, messages.SUCCESS, f"Комментарий опубликован")
        elif action == 'delete':
            comment_services.CommentHandler.delete_comment_by_seller(comment_id)
            messages.add_message(self.request, messages.SUCCESS, f"Комментарий опубликован")
        else:
            comment_services.CommentHandler.set_comment_reject(comment_id)
            messages.add_message(self.request, messages.WARNING, f"Комментарий снят с публикации")

        query_string = request.META.get('HTTP_REFERER').split('?')[1]
        url = redirect('app_store:comment_list').url
        path = '?'.join([url, query_string])
        return redirect(path)


# EXPORT & IMPORT DATA-STORE FUNCTION #
def export_data_to_csv(*args, **kwargs):
    """Функция для экспорта данных из магазина продавца в формате CSV."""
    store_id = kwargs['pk']
    store = store_models.Store.active_stores.get(id=store_id)
    items = item_models.Item.objects.filter(store__id=store_id)
    curr_date = datetime.now().strftime('%Y-%m-%d')
    response = HttpResponse()
    response['Content-Disposition'] = f'attachment; filename="price_list_{curr_date}({store.title})"'
    writer = csv.writer(response)
    # writer.writerow(['id', 'title', 'stock', 'price'])
    items_report = items.values_list(
        'id',
        'title',
        'stock',
        'price',
        'is_available',
        'category__title',
        'store__title',
    )
    for item in items_report:
        writer.writerow(item)
    return response


def import_data_from_cvs(request, **kwargs):
    """Функция для импорта данных в магазин продавца и создание новых позиций товаров."""
    store = kwargs['pk']
    if request.method == 'POST' and request.FILES["file"]:
        # allowed_types = ['.cvs', ]
        form = store_forms.ImportDataFromCVS(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.cleaned_data.get('file')
            file_name = upload_file.name.split('.')[0]
            handle_uploaded_file(upload_file, file_name)
            with open(f'fixtures/{file_name}.htm', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    _, created = item_models.Item.objects.update_or_create(
                        id=row[0],
                        title=row[1],
                        defaults={'price': row[3], 'stock': row[2]},
                    )
                messages.success(request, "Фикстуры успешно загружены.")
            return redirect('app_store:store_detail', store)
        else:
            return redirect('app_store:store_detail', store)


def handle_uploaded_file(f, name):
    """Функция создания файла с фикстурами."""
    with open(f'fixtures/{name}.htm', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
