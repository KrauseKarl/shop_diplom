import csv
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.db.models import Sum, Q
from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic
from django.http import HttpResponse
# models
from app_cart import models as cart_models
from app_item import models as item_models
from app_order import models as order_models
from app_settings.models import SiteSettings
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
from app_order.tasks import delivery_in_progress
from utils.my_utils import MixinPaginator, SellerOnlyMixin


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
                prefetch_related('tag', 'views', 'image', 'feature_value'). \
                filter(
                Q(title__icontains=title) |
                Q(title__icontains=lower)
            ).distinct()
        if request.GET.get('order_by', None):
            order_by = request.GET.get('order_by')
            items = store_services.StoreHandler.ordering_store_items(queryset=items, order_by=order_by)
            context['message'] = store_services.StoreHandler.ordering_message(order_by=order_by)

        context['categories'] = item_services.CategoryHandler.get_categories_in_items_set(all_items)
        context['object_list'] = self.my_paginator(items, self.request, 7)
        context['total_profit'] = store_services.StoreHandler.total_profit_store(store)

        return self.render_to_response(context)


class CreateStoreView(SellerOnlyMixin, generic.CreateView):
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


class StoreUpdateViews(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для обновления магазина."""
    model = store_models.Store
    template_name = 'app_store/store/store_edit.html'
    context_object_name = 'store'
    form_class = store_forms.UpdateStoreForm

    def test_func(self):
        user = self.request.user
        store = self.get_object()
        return True if user == store.owner else False

    def get_success_url(self):
        store = self.get_object()
        return redirect('app_store:store_detail', store.pk)


# ITEM VIEWS #


class CreateItemView(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания и добавления товара в магазин магазина."""
    model = store_models.Store
    template_name = 'app_store/item/add_item.html'
    form_class = store_forms.AddItemImageForm
    second_form_class = store_forms.TagFormSet

    def get(self, *args, **kwargs):
        formset_tag = store_forms.TagFormSet(queryset=item_models.Tag.objects.none())
        formset_image = store_forms.ImageFormSet(queryset=item_models.Image.objects.none())
        context = {
            'tag_formset': formset_tag,
            'image_formset': formset_image,
            'form': self.form_class,
            'colors': item_services.get_colors(item_models.Item.available_items.all())
        }
        return self.render_to_response(context=context)

    def form_valid(self, form):
        with transaction.atomic():
            item = form.save(commit=False)
            item.is_active = True
            item.save()
            if len(self.request.FILES.getlist('image')) == 1:
                img = self.request.FILES.getlist('image')[0]
                image = item_models.Image.objects.create(image=img, title=item.title)
                item.image.add(image.id)
                item.save()
            else:
                for img in self.request.FILES.getlist('image'):
                    image = item_models.Image.objects.create(image=img, title=item.title)
                    item.image.add(image.id)
                    item.save()
            store_id = self.kwargs['pk']
            store = store_services.StoreHandler.get_store(store_id)
            store.items.add(item)
            store.save()
            messages.add_message(self.request, messages.INFO, f"Товаре {item} добавлен")
        return redirect('app_store:store_detail', store.pk)

    def form_invalid(self, form):
        context = {
            'message': 'error',
            'tags': item_models.Tag.objects.all(),
            'colors': item_services.get_colors(item_models.Item.objects.all())
        }
        return render(self.request, self.template_name, context=context)


class UpdateItemView(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для обновления товара."""
    model = item_models.Item
    template_name = 'app_store/item/edit_item.html'
    form_class = store_forms.UpdateItemImageForm
    second_form_class = store_forms.ImageFormSet
    extra_context = {'colors': item_services.get_colors(item_models.Item.available_items.all()),
                     'image_formset': store_forms.ImageFormSet(queryset=item_models.Image.objects.none())}

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
        form = store_forms.UpdateItemImageForm(data=self.request.POST, instance=self.get_object(),
                                               files=self.request.FILES)
        item = form.save(commit=False)
        for new_value in self.request.POST.getlist('value'):
            feature = item_models.Feature.objects.filter(values=new_value)
            if feature:
                if item.feature_value.all():
                    for old_value in item.feature_value.all():
                        if old_value.feature == feature:
                            item.feature_value.remove(old_value)
                item.feature_value.add(new_value)
                item.save()
        for img in self.request.FILES.getlist('image'):
            image = item_models.Image.objects.create(image=img, title=item.title)
            if image not in item.image.all():
                item.image.add(image.id)
                item.save()
        item.save()
        messages.add_message(self.request, messages.SUCCESS, f"Данные о товаре {item} обновлены")
        return super().form_invalid(form)

    def get_success_url(self):
        item = self.get_object()
        store_id = item.store.id
        return reverse('app_store:store_detail', kwargs={'pk': store_id})


class DeleteItem(UserPassesTestMixin, generic.DeleteView):
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
            item.delete()
            messages.add_message(self.request, messages.ERROR, f"Товар {item} успешно удален")
            return redirect('app_user:account', user.pk)
        except ObjectDoesNotExist:
            raise Http404("Такой товар не существует")


# CATEGORY VIEW #


class CategoryListView(SellerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех категорий товаров."""
    model = item_models.Category
    template_name = 'app_store/category/category_list.html'
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
        categories = self.my_paginator(categories, self.request, self.paginate_by)
        context = {'object_list': categories, 'alphabet': alphabet_list}
        return render(request, self.template_name, context)


class CategoryCreateView(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания категории товаров."""
    model = item_models.Category
    template_name = 'app_store/category/category_list.html'
    form_class = store_forms.CreateCategoryForm

    def form_valid(self, form):
        form.save()
        category_title = form.cleaned_data.get('title')
        messages.add_message(self.request, messages.SUCCESS, f'Категория - "{category_title}" создана')
        return redirect('app_store:category_list')

    def form_invalid(self, form):
        form = store_forms.CreateCategoryForm(self.request.POST)
        return super(CategoryCreateView, self).form_invalid(form)


# TAG VIEWS #


class AddTagView(SellerOnlyMixin, generic.UpdateView):
    """Класс-представление для  добавления тега в карточку товара."""
    model = item_models.Item
    template_name = 'app_store/add_tag.html'
    form_class = store_forms.AddTagForm

    # extra_context = {} # TODO don't work with DOCKER
    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        tag = self.get_object()
        context = {
            'tag_book': item_services.TagHandler.get_abc_ordered(),
        }
        return render(request, self.template_name, context=context)

    def form_valid(self, form):
        form.save()
        item_id = self.kwargs['pk']
        item = item_models.Item.objects.get(id=item_id)
        messages.add_message(self.request, messages.INFO, f"Новый тег успешно добавлен")

        return redirect('app_store:edit_item', item.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class TagListView(SellerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех тегов товаров."""
    model = item_models.Tag
    template_name = 'app_store/tag_list.html'
    paginate_by = 20

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:

        alphabet_list = sorted(set([tag.title[0] for tag in item_models.Tag.objects.order_by('title')]))
        sort_by_letter = request.GET.get('sort_by_letter')
        if sort_by_letter:
            tag_set = item_models.Tag.objects.filter(title__istartswith=sort_by_letter)
        else:
            tag_set = item_models.Tag.objects.all()
        object_list = self.my_paginator(tag_set, self.request, self.paginate_by)
        context = {'object_list': object_list, 'alphabet': alphabet_list}
        return render(request, self.template_name, context)


class CreateTagView(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания категории товаров."""
    model = item_models.Category
    template_name = 'app_store/tag_list.html'
    form_class = store_forms.CreateTagForm

    def form_valid(self, form):
        form.save()
        tag_title = form.cleaned_data.get('title').upper()
        messages.add_message(self.request, messages.SUCCESS, f'Тег - "{tag_title}" создан')
        return redirect('app_store:tag_list')

    def form_invalid(self, form):
        form = store_forms.CreateTagForm(self.request.POST)
        return super(CreateTagView, self).form_invalid(form)


class DeleteTag(generic.DeleteView):
    """Класс-представление для удаления тега из карточки товара"""
    model = item_models.Tag

    def get(self, request, *args, **kwargs):
        item_id = kwargs['item_id']
        item = item_models.Item.objects.get(id=item_id)
        tag_id = kwargs['tag_id']
        tag = item_models.Tag.objects.get(id=tag_id)
        if tag in item.tag.all():
            item.tag.remove(tag)
        item.save()
        messages.add_message(self.request, messages.INFO, f"Тег  {tag} успешно удален")
        return redirect('app_store:edit_item', item.pk)


# IMAGE VIEWS #
class DeleteImage(UserPassesTestMixin, generic.DeleteView):
    """Класс-представление для удаления изображения из карточки товара"""
    model = item_models.Image

    def test_func(self):
        user = self.request.user
        image = self.get_object()
        return True if user == image.item.first.store.owner else False

    def get(self, request, *args, **kwargs):
        item_id = kwargs['item_id']
        item = item_models.Item.available_items.get(id=item_id)
        image_id = kwargs['image_id']
        image = item_models.Image.objects.get(id=image_id)
        if image in item.image.all():
            item.image.remove(image)
            item_models.Image.objects.filter(id=image.id).delete()
        item.save()
        messages.add_message(self.request, messages.INFO, f"Изображение успешно удалено")
        return redirect('app_store:edit_item', item.pk)


# FEATURE VIEWS #

class FeatureListView(SellerOnlyMixin, generic.DetailView):
    model = item_models.Category
    template_name = 'app_store/features/feature_list.html'

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        super(FeatureListView, self).get(request, *args, **kwargs)
        category = self.get_object()
        features = item_models.Feature.objects.prefetch_related('categories').filter(categories=category)
        feature = self.request.GET.get('feature')
        if feature:
            feature = features.filter(title=feature).first()
            values = item_models.FeatureValue.objects.select_related('feature').filter(feature=feature.id)
        else:
            values = item_models.FeatureValue.objects.select_related('feature').filter(feature__in=features)

        context = {'features': features, 'category': category, 'values': values}
        return render(request, self.template_name, context)


class CreateFeatureView(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания характеристики  товаров."""
    model = item_models.Feature
    template_name = 'app_store/features/feature_list.html'
    form_class = store_forms.CreateFeatureForm

    def form_valid(self, form):
        feature = form.save()
        category_id = form.cleaned_data.get('category')
        category = item_models.Category.objects.get(id=category_id)
        feature.categories.add(category.id)
        messages.add_message(self.request, messages.SUCCESS, f'Характеристика - "{feature}" добавлено')
        return redirect('app_store:feature_list', category.slug)

    def form_invalid(self, form):
        form = store_forms.CreateTagForm(self.request.POST)
        return super(CreateFeatureView, self).form_invalid(form)


class CreateFeatureValueView(SellerOnlyMixin, generic.CreateView):
    """Класс-представление для создания значения характеристики  товаров."""
    model = item_models.FeatureValue
    template_name = 'app_store/features/feature_list.html'
    form_class = store_forms.CreateValueForm

    def form_valid(self, form):
        feature_value = form.save()
        feature = feature_value.feature
        category = item_models.Category.objects.get(feature=feature)
        messages.add_message(self.request, messages.SUCCESS, f'Значение - "{feature_value}" добавлено')
        return redirect('app_store:feature_list', category.slug)

    def form_invalid(self, form):
        form = store_forms.CreateTagForm(self.request.POST)
        return super(CreateFeatureValueView, self).form_invalid(form)


# DELIVERY VIEWS #


class DeliveryListView(SellerOnlyMixin, generic.ListView):
    """Класс-представление для отображения списка всех заказов продавца."""
    model = order_models.Order
    template_name = 'app_store/delivery/delivery_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        stores = store_models.Store.objects.filter(owner=self.request.user)
        queryset = order_models.Order.objects.filter(store__in=stores)
        return queryset

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        orders = self.get_queryset()
        item_quantity = None
        if self.request.GET.get('store'):
            current_store = self.request.GET.get('store')
            orders = orders.filter(order__store__title=current_store)
        if request.GET.get('status'):
            status = request.GET.get('status')
            orders = orders.filter(status=status)
            item_quantity = orders.aggregate(total=Sum('item__quantity')).get('total')

        if request.GET.get('number'):
            order_number = request.GET.get('number')
            orders = orders.filter(order__id__icontains=order_number)
        context = {
            'orders': orders,
            'status_list': order_models.OrderItem.STATUS,
            'item_quantity': item_quantity,
        }

        return render(request, self.template_name, context=context)


class DeliveryDetailView(UserPassesTestMixin, generic.DetailView):
    """Класс-представление для отображения одного заказа в магазине продавца."""
    model = order_models.Order
    template_name = 'app_store/delivery/delivery_detail.html'
    context_object_name = 'order'

    def test_func(self):
        # user = self.request.user
        # order = self.get_object()
        return True #if user == order.store.all()  else False

    def get(self, request, *args, category=None, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        stores = request.user.store.all()
        order = self.get_object()
        context['items'] = order.order_items.filter(item__item__store__in=stores)
        context['total'] = context['items'].aggregate(total_cost=Sum('total')).get('total_cost')
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
        print(form)
        form.save()
        order = self.get_object()
        messages.add_message(self.request, messages.SUCCESS, f"Данные {order} успешно обновлены")
        return redirect('app_store:delivery_detail', order.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class OrderItemUpdateView(generic.UpdateView):
    model = order_models.OrderItem
    template_name = 'app_store/delivery/delivery_edit.html'
    form_class = order_form.OrderItemUpdateForm
    context_object_name = 'order_item'

    def form_valid(self, form):
        order_item = form.save()
        order_item.quantity = form.cleaned_data.get('quantity')
        order_item.total = order_item.item.price * form.cleaned_data.get('quantity')
        order_item.save()
        order_id = order_item.order.id
        order = order_models.Order.objects.get(id=order_id)
        store = order.store.first()
        new_total_order = 0
        for order_item in order.order_items.all():
            if order_item.total > store.min_for_discount:
                new_total_order += round(float(order_item.total) * ((100 -store.discount) / 100), 0)
            else:
                new_total_order += float(order_item.total)
        min_free_delivery = SiteSettings().min_free_delivery
        delivery_fees = SiteSettings().delivery_fees
        express_delivery_fees = SiteSettings().express_delivery_price
        if new_total_order < min_free_delivery:
           new_delivery_fees = delivery_fees
        else:
            new_delivery_fees = 0
        if order.delivery == 'express':
            new_delivery_fees += express_delivery_fees
        order.total_sum = new_total_order + new_delivery_fees
        order.delivery_fees = new_delivery_fees
        order.save()

        messages.add_message(self.request, messages.SUCCESS, f"Количество товара({self.get_object()}) в заказе обновлено.")


        return redirect('app_store:order_item_edit', self.get_object().pk)

    def form_invalid(self, form):
        order_item = self.get_object()
        messages.add_message(self.request, messages.ERROR,
                             f"Произошла ошибка при обновлении количества товара в заказе.")
        return redirect('app_store:order_item_edit', order_item.pk)


class SentPurchase(generic.UpdateView):
    """Класс-представление для отправки товара покупателю."""
    model = order_models.Order
    template_name = 'app_store/delivery/delivery_detail.html'
    context_object_name = 'order'
    form_class = store_forms.UpdateOrderStatusForm

    def post(self, request, *args, **kwargs):
        order_id = self.kwargs['order_id']
        order = order_models.Order.objects.get(id=order_id)
        form = store_forms.UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.save()

            delivery_in_progress.delay(order.id)
            path = self.request.META.get('HTTP_REFERER')
            messages.success(self.request, f"Заказ  {order} отправлен")
            return redirect(path)


class CommentListView(generic.ListView):
    """Класс-представление для отображения списка всех заказов продавца."""
    model = item_models.Comment
    template_name = 'app_store/comment/comment_list.html'
    context_object_name = 'comments'

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        comments = store_services.SellerOrderHAndler.get_seller_comment_list(request)
        if self.request.GET.get('store'):
            current_store = self.request.GET.get('store')
            comments = comments.filter(item__store__slug=current_store)
        if request.GET.get('is_published'):
            status = request.GET.get('is_published')
            comments = comments.filter(is_published=status)
        else:
            comments = comments
        return render(request, self.template_name, {'object_list': comments})


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


class CommentDetail(generic.DetailView):
    """Класс-представление для отображения одного комментария."""
    model = item_models.Comment
    template_name = 'app_store/comment/comment_detail.html'
    context_object_name = 'comment'


class CommentDelete(generic.DeleteView):
    """Класс-представление для удаления комментария."""
    model = item_models.Comment
    template_name = 'app_store/comment/comment_delete.html'

    def form_valid(self, form):
        success_url = self.success_url
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())


class CommentModerate(generic.UpdateView):
    """Класс-представление для изменения статуса комментария(прохождение модерации)."""
    model = item_models.Comment
    template_name = 'app_store/comment/comment_update.html'
    fields = ['is_published']


# EXPORT & IMPORT DATA-STORE FUNCTION #
def export_data_to_csv(request, **kwargs):
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
