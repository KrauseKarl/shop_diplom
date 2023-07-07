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
            'colors': item_services.ItemHandler.colors,
            'category_set': item_models.Category.objects.all()
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
            messages.add_message(self.request, messages.SUCCESS, f"Товаре {item} создан")
            messages.add_message(self.request, messages.INFO,
                                 "Новый товар еще не активирован. Активируйте товар на странице товара")
        return redirect('app_store:store_detail', store.pk)

    def form_invalid(self, form):
        # form = store_forms.AddItemImageForm(self.request.POST, self.request.FILES)
        print(form.errors)
        messages.add_message(self.request, messages.ERROR, f"Ошибка. Товар не создан. Повторите попытку.")
        return super().form_invalid(form)


class ItemUpdateView(UserPassesTestMixin, generic.UpdateView):
    """Класс-представление для обновления товара."""
    model = item_models.Item
    template_name = 'app_store/item/edit_item.html'
    form_class = store_forms.UpdateItemForm
    second_form_class = store_forms.UpdateItemImageForm

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
        try:
            item = item_models.Item.objects.get(id=kwargs['pk'])
            if item.is_active:
                item.is_active = False
                item.is_available = True
                message = f"Товар {item} успешно восстановлен"
            else:
                item.is_active = True
                item.is_available = False
                message = f"Товар {item} успешно удален"
            item.save(update_fields=['is_available', 'is_active'])
            messages.add_message(self.request, messages.WARNING, message)
            return redirect('app_store:edit_item', item.pk)
        except ObjectDoesNotExist:
            raise Http404("Такой товар не существует")


# TAG VIEWS #
class TagListView(SellerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех тегов товаров."""
    model = item_models.Tag
    template_name = 'app_store/tag/tag_list.html'
    paginate_by = 20

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:

        alphabet_list = sorted(set([tag.title[0] for tag in item_models.Tag.objects.order_by('title')]))
        sort_by_letter = request.GET.get('sort_by_letter')
        if sort_by_letter:
            tag_set = item_models.Tag.objects.filter(title__istartswith=sort_by_letter)
        else:
            tag_set = item_models.Tag.objects.all()
        object_list = MixinPaginator(tag_set, self.request, self.paginate_by).my_paginator()
        context = {'object_list': object_list, 'alphabet': alphabet_list}
        return render(request, self.template_name, context)


class AddTagToItem(SellerOnlyMixin, generic.UpdateView):
    """Класс-представление для  добавления тега в карточку товара."""
    model = item_models.Item
    context_object_name = 'item'
    template_name = 'app_store/tag/add_tag.html'
    form_class = store_forms.AddTagForm
    MESSAGE = "Новый тег(и) успешно добавлен(ы)"

    def form_valid(self, form):
        tag_list = form.cleaned_data.get('tag')
        item = item_models.Item.objects.get(id=self.kwargs['pk'])
        for t in tag_list:
            tag = item_models.Tag.objects.get(id=t.id)
            item.tag.add(tag)
            item.save()
        messages.add_message(self.request, messages.INFO, self.MESSAGE)
        return redirect('app_store:edit_item', item.pk)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, f"{form.errors}")
        return self.render_to_response(self.get_context_data(form=form))


class RemoveTagFromItem(generic.DeleteView):
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
        messages.add_message(self.request, messages.WARNING, f"Тег {tag} успешно удален")
        return redirect('app_store:edit_item', item.pk)


# FEATURE VALUE
class RemoveFeatureValueView(SellerOnlyMixin, generic.DeleteView):
    model = item_models.FeatureValue


    def get(self, request, *args, **kwargs): # TODO  RemoveFeatureValueView
        # value = self.get_object()
        # item = image.item_images.first()
        # if image in item.images.all():
        #     item.images.remove(image)
        #     item_models.Image.objects.filter(id=image.id).delete()
        # item.save()
        # messages.add_message(self.request, messages.WARNING, self.MESSAGE)
        # return redirect('app_store:edit_item', item.pk)
        pass


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


# DELIVERY VIEWS #
class DeliveryListView(SellerOnlyMixin, generic.ListView):
    """Класс-представление для отображения списка всех заказов продавца."""
    model = order_models.Order
    template_name = 'app_store/delivery/delivery_list.html'
    context_object_name = 'orders'
    STATUS_LIST = order_models.Order().STATUS
    paginate_by = 4

    def get_queryset(self):
        queryset = order_services.SellerOrderHAndler.get_seller_order_list(owner=self.request.user)
        return queryset

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        object_list = self.get_queryset()
        if self.request.GET:
            # STORE
            if self.request.GET.get('stores'):
                stores = self.request.GET.getlist('stores')
                object_list = object_list.filter(store__title__in=stores)
            # STATUS
            if self.request.GET.get('status'):
                status = self.request.GET.getlist('status')
                object_list = object_list.filter(status__in=status)
            # SEARCH
            if self.request.GET.get('search'):
                search = self.request.GET.get('search')
                object_list = object_list.filter(id=search)
        object_list = MixinPaginator(
            request=request,
            object_list=object_list, 
            per_page=self.paginate_by
        ).my_paginator()
        print(object_list)
        context = {
            'object_list': object_list,
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
    MESSAGE_SUCCESS = "Данные заказа успешно обновлены"
    MESSAGE_ERROR = "Ошибка обновления данных заказа"

    def test_func(self):
        user = self.request.user
        order = self.get_object()
        return True if user == order.store.first().owner else False

    def form_valid(self, form):
        form.save()
        order = self.get_object()
        messages.add_message(self.request, messages.SUCCESS, self.MESSAGE_SUCCESS)
        return redirect('app_store:delivery_detail', order.pk)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, self.MESSAGE_ERROR)
        return self.render_to_response(self.get_context_data(form=form))


class OrderItemUpdateView(generic.UpdateView):
    """Класс-представление для обновления кол-во товаров в заказе."""
    model = order_models.OrderItem
    template_name = 'app_store/delivery/delivery_edit.html'
    form_class = order_form.OrderItemUpdateForm
    context_object_name = 'order_item'
    MESSAGE_SUCCESS = "Количество товара обновлено."
    MESSAGE_ERROR = "Произошла ошибка при обновлении количества товара."

    def form_valid(self, form):
        order_services.SellerOrderHAndler.update_item_in_order(self.request, form)
        messages.add_message(self.request, messages.SUCCESS, self.MESSAGE_SUCCESS)
        return redirect('app_store:order_item_edit', self.get_object().pk)

    def form_invalid(self, form):
        order_item = self.get_object()
        messages.add_message(self.request, messages.ERROR, self.MESSAGE_ERROR)
        return redirect('app_store:order_item_edit', order_item.pk)


class SentPurchase(generic.UpdateView):
    """Класс-представление для отправки товара покупателю."""
    model = order_models.OrderItem
    template_name = 'app_store/delivery/delivery_detail.html'
    context_object_name = 'order'
    form_class = store_forms.UpdateOrderStatusForm
    MESSAGE_ERROR = "Произошла ошибка при отправки заказа."

    def form_valid(self, form):
        super().form_invalid(form)
        form.save()
        status = form.cleaned_data['status']
        order_item_id = self.kwargs['pk']
        order_item = order_services.SellerOrderHAndler.sent_item(order_item_id, status)
        tasks.check_order_status.delay(order_item.order.id)
        messages.add_message(self.request, messages.SUCCESS, f"{order_item} отправлен")
        return redirect(self.request.META.get('HTTP_REFERER'))

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, self.MESSAGE_ERROR)
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
        'category__id',
        'store__id',
        'color',

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
            with open(f'fixtures/{file_name}.txt', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    category = item_models.Category.objects.filter(id=row[5]).first()
                    store = store_models.Store.objects.filter(id=row[6]).first()
                    _, created = item_models.Item.objects.update_or_create(
                        id=row[0],
                        title=row[1],
                        defaults={
                            'stock': row[2],
                            'price': row[3],
                            'is_available': row[4],
                            'category': category,
                            'store': store,
                            'color': row[7],
                            },
                    )
                messages.add_message(request, messages.SUCCESS, "Фикстуры успешно загружены.")
            return redirect('app_store:store_detail', store.id)
        else:
            return redirect('app_store:store_detail', store.id)


def handle_uploaded_file(f, name):
    """Функция создания файла с фикстурами."""
    with open(f'fixtures/{name}.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
