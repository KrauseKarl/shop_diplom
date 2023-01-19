import csv
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.http import HttpResponse

from app_user.forms import UpdateUserForm, UpdateProfileForm
from app_user.models import Profile
from app_user.services.register_services import ProfileHandler
from utils.my_utils import MixinPaginator
from app_cart.models import CartItem
from app_item.models import Item, Tag, Image, Category
from app_item.services.item_services import TagHandler, CategoryHandler, get_colors, ItemHandler
from app_order.models import Order, Invoice
from app_store.models import Store
from app_store.services.store_services import StoreHandler
from app_store.form import (
    CreateStoreForm,
    AddItemForm,
    TagFormSet,
    AddTagForm,
    UpdateItemForm,
    CreateTagForm,
    ImageFormSet,
    ImportDataFromCVS,
    UpdateStoreForm,
    UpdateOrderStatusForm,
    CreateCategoryForm
)


# STORE VIEWS #


class StoreListView(ListView):
    # TODO StoreListView description
    model = Store
    template_name = 'app_store/store/store_list.html'
    context_object_name = 'stores'

    def queryset(self):
        owner = self.request.user
        queryset = StoreHandler.get_all_story_by_owner(owner)
        return queryset


class StoreDetailView(DetailView, MixinPaginator):
    # TODO StoreDetailView description
    model = Store
    template_name = 'app_store/store/store_detail.html'
    context_object_name = 'store'

    def get(self, request, *args, category=None, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)

        store = self.get_object()
        all_items = store.items.all()

        try:
            category_slug = kwargs['slug']
            category = CategoryHandler.get_categories(category_slug)
            items = all_items.filter(category=category)
        except (ObjectDoesNotExist, KeyError):
            items = all_items

        if request.GET.get('order_by', None):
            order_by = request.GET.get('order_by')
            items = StoreHandler.ordering_store_items(queryset=items, order_by=order_by)
            context['message'] = StoreHandler.ordering_message(order_by=order_by)

        context['categories'] = CategoryHandler.get_categories_in_items_set(all_items)
        context['object_list'] = self.my_paginator(items, self.request, 7)
        context['total_profit'] = StoreHandler.total_profit_store(store)

        return self.render_to_response(context)


class StoreUpdateViews(UpdateView):
    # TODO StoreUpdateViews description
    model = Store
    template_name = 'app_store/store/store_edit.html'
    context_object_name = 'store'
    form_class = UpdateStoreForm

    def get_success_url(self):
        store = self.get_object()
        return redirect('app_store:store_detail', store.pk)


class CreateStoreView(CreateView):
    # TODO CreateStoreView description
    model = Store
    template_name = 'app_store/store/create_store.html'
    form_class = CreateStoreForm

    def form_valid(self, form):
        store = form.save()
        store.is_active = True
        store.owner = self.request.user
        store.save()
        return redirect('app_store:store_detail', store.pk)


# SELLER VIEWS #
class DetailAccount(DetailView):
    # TODO DetailAccount description
    model = User
    template_name = 'seller/account.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        if user.profile.role == 'CSR':
            context['order'] = Order.objects.filter(user=self.get_object()).last()
        return context


class UpdateProfile(UpdateView):
    # TODO UpdateProfile description
    model = User
    second_model = Profile
    template_name = 'seller/profile_edit.html'
    form_class = UpdateUserForm
    second_form_class = UpdateProfileForm

    def form_valid(self, form):
        user_form = UpdateUserForm(
            data=self.request.POST,
            instance=self.request.user
        )
        profile_form = UpdateProfileForm(
            data=self.request.POST,
            files=self.request.FILES,
            instance=self.request.user.profile
        )
        user_form.save()
        profile = profile_form.save(commit=False)
        telephone = profile_form.cleaned_data['telephone']
        telephone = ProfileHandler.telephone_formatter(telephone)
        profile.telephone = telephone
        profile.save()
        messages.success(self.request, "Данные профиля обновлены!")
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        pk = self.kwargs["pk"]
        return reverse('app_user:account', kwargs={'pk': pk})


# ITEM VIEWS #


class AddItemView(CreateView):
    # TODO AddItemView description
    model = Item
    template_name = 'app_store/item/add_item.html'
    form_class = AddItemForm
    second_form_class = TagFormSet

    def get(self, *args, **kwargs):
        formset_tag = TagFormSet(queryset=Tag.objects.none())
        formset_image = ImageFormSet(queryset=Image.objects.none())
        context = {
            'tag_formset': formset_tag,
            'image_formset': formset_image,
            'form': self.form_class,
            'colors': get_colors(Item.available_items.all())
        }
        return self.render_to_response(context=context)

    def form_valid(self, form):
        with transaction.atomic():
            item = form.save(commit=False)
            item.is_active = True
            item.save()
            if len(self.request.FILES.getlist('image')) == 1:
                img = self.request.FILES.getlist('image')[0]
                image = Image.objects.create(image=img, title=item.title)
                item.image.add(image.id)
                item.save()
            else:
                for img in self.request.FILES.getlist('image'):
                    image = Image.objects.create(image=img, title=item.title)
                    item.image.add(image.id)
                    item.save()
            store_id = self.kwargs['pk']
            store = StoreHandler.get_store(store_id)
            store.items.add(item)
            store.save()

        return redirect('app_store:store_detail', store.pk)

    def form_invalid(self, form):
        context = {
            'message': 'error',
            'tags': Tag.objects.all(),
            'colors': get_colors(Item.objects.all())
        }
        return render(self.request, self.template_name, context=context)


class UpdateItemView(UpdateView):
    # TODO UpdateItemView description
    model = Item
    template_name = 'app_store/item/edit_item.html'
    form_class = UpdateItemForm
    second_form_class = ImageFormSet
    extra_context = {'colors': get_colors(Item.available_items.all()),
                     'image_formset': ImageFormSet(queryset=Image.objects.none())}

    def get(self, *args, **kwargs):
        formset_tag = TagFormSet(queryset=Tag.objects.none())
        formset_image = ImageFormSet(queryset=Image.objects.none())
        context = {
            'tag_formset': formset_tag,
            'image_formset': formset_image,
            'form': self.form_class,
            'colors': get_colors(Item.objects.all()),
            'item': self.get_object(),
        }
        return self.render_to_response(context=context)

    def form_valid(self, form):
        form = UpdateItemForm(data=self.request.POST, instance=self.get_object(), files=self.request.FILES)
        item = form.save(commit=False)
        for img in self.request.FILES.getlist('image'):
            image = Image.objects.create(image=img, title=item.title)
            if image not in item.image.all():
                item.image.add(image.id)
                item.save()
        item.save()

        messages.success(self.request, f"Данные о товаре {item} обновлены")
        return super().form_invalid(form)

    def get_success_url(self):
        item = self.get_object()
        store = self.request.user.store.all()
        store_id = store.filter(items=item)
        return reverse('app_store:store_detail', kwargs={'pk': store_id})


class DeleteItem(DeleteView):
    model = Item

    def get(self, request, *args, **kwargs):
        item_id = kwargs['item_id']
        user = self.request.user
        try:
            item = ItemHandler.get_item(item_id)
            item.delete()
            messages.success(self.request, f"Товар {item} успешно удален")

            return redirect('app_user:account', user.pk)
        except ObjectDoesNotExist:
            raise Http404("Такой товар не существует")


# CATEGORY VIEW #


class CategoryListView(ListView, MixinPaginator):
    # TODO CategoryListView description
    model = Category
    template_name = 'app_store/category/category_list.html'
    extra_context = {'alphabet': [category.title[0] for category in Category.objects.all()]}
    paginate_by = 5

    def get(self, request, *args, **kwargs):
        alphabet_list = sorted(set([category.title[0] for category in Category.objects.order_by('title')]))
        sort_by_letter = request.GET.get('sort_by_letter')
        if sort_by_letter:
            categories = Category.objects.filter(title__istartswith=sort_by_letter)
        else:
            categories = Category.objects.all()
        categories = self.my_paginator(categories, self.request, self.paginate_by)
        context = {'object_list': categories, 'alphabet': alphabet_list}
        return render(request, self.template_name, context)


class CategoryCreateView(CreateView):
    # TODO CategoryCreateView description
    model = Category
    template_name = 'app_store/category/category_list.html'
    form_class = CreateCategoryForm

    def form_valid(self, form):
        form.save()
        category_title = form.cleaned_data.get('title')
        messages.success(self.request, f'Категория - "{category_title}" создана')
        return redirect('app_store:category_list')

    def form_invalid(self, form):
        form = CreateCategoryForm(self.request.POST)
        return super(CategoryCreateView, self).form_invalid(form)


# TAG VIEWS #


class AddTagView(UpdateView):
    # TODO AddTagView description
    model = Item
    template_name = 'app_store/add_tag.html'
    form_class = AddTagForm
    extra_context = {'tag_book': TagHandler.get_abc_ordered()}

    def form_valid(self, form):
        form.save()
        item_id = self.kwargs['pk']
        item = Item.objects.get(id=item_id)
        messages.success(self.request, f"Новый тег успешно добавлен")
        return redirect('app_store:edit_item', item.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CreateTagView(CreateView):
    model = Tag
    template_name = 'app_store/add_tag.html'
    form_class = CreateTagForm


class DeleteTag(DeleteView):
    model = Tag

    def get(self, request, *args, **kwargs):
        item_id = kwargs['item_id']
        item = Item.objects.get(id=item_id)
        tag_id = kwargs['tag_id']
        tag = Tag.objects.get(id=tag_id)
        if tag in item.tag.all():
            item.tag.remove(tag)
        item.save()
        messages.success(self.request, f"Тег  {tag} успешно удален")
        return redirect('app_store:edit_item', item.pk)


# IMAGE VIEWS #
class DeleteImage(DeleteView):
    # TODO DeleteImage description
    model = Image

    def get(self, request, *args, **kwargs):
        item_id = kwargs['item_id']
        item = Item.available_items.get(id=item_id)
        image_id = kwargs['image_id']
        image = Image.objects.get(id=image_id)
        if image in item.image.all():
            item.image.remove(image)
            Image.objects.filter(id=image.id).delete()
        item.save()
        return redirect('app_store:edit_item', item.pk)


# DELIVERY VIEWS #


class DeliveryListView(ListView):
    # TODO DeliveryListView description
    model = Order
    template_name = 'app_store/delivery/delivery_list.html'
    context_object_name = 'orders'

    def get(self, request, status=None, **kwargs):
        super().get(request, **kwargs)
        owner = self.request.user
        stores = Store.active_stores.filter(owner=owner)

        items = Item.available_items.filter(store__in=stores)
        items_in_cart = CartItem.objects.filter(item_id__in=items)
        orders = Order.objects.filter(items_is_paid__in=items_in_cart).distinct().order_by('-created')
        if status:
            orders = orders.filter(status=status)
        else:
            orders = orders
        return render(request, self.template_name, {'orders': orders})


class DeliveryDetailView(DetailView):
    # TODO DeliveryDetailView description
    model = Order
    template_name = 'app_store/delivery/delivery_detail.html'
    context_object_name = 'order'

    def get(self, request, *args, category=None, **kwargs):
        super().get(request, *args, **kwargs)
        context = self.get_context_data(object=self.object)
        stores = request.user.store.all()
        order = self.get_object()
        context['items'] = CartItem.objects.filter(item__store__in=stores).filter(order=order)
        return self.render_to_response(context)


class SentPurchase(UpdateView):
    # TODO SentPurchase description
    model = Order
    template_name = 'app_store/delivery/delivery_detail.html'
    context_object_name = 'order'
    form_class = UpdateOrderStatusForm

    def post(self, request, *args, **kwargs):
        order_id = self.kwargs['order_id']
        order = Order.objects.get(id=order_id)
        form = UpdateOrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            order.status = status
            order.save()
            path = self.request.META.get('HTTP_REFERER')
            messages.success(self.request, f"Заказ  {order} отправлен")
            return redirect(path)


# EXPORT & IMPORT DATA-STORE FUNCTION #
def export_data_to_csv(request, **kwargs):
    # TODO export_data_to_csv description
    store_id = kwargs['pk']
    store = Store.active_stores.get(id=store_id)
    items = Item.available_items.filter(store_items__id=store_id)
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
        'store_items__title',
    )
    for item in items_report:
        writer.writerow(item)
    return response


def import_data_from_cvs(request, **kwargs):
    # TODO import_data_from_cvs description
    store = kwargs['pk']
    if request.method == 'POST' and request.FILES["file"]:
        # allowed_types = ['.cvs', ]
        form = ImportDataFromCVS(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.cleaned_data.get('file')
            file_name = upload_file.name.split('.')[0]
            handle_uploaded_file(upload_file, file_name)
            with open(f'fixtures/{file_name}.htm', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    _, created = Item.objects.update_or_create(id=row[0],
                                                               title=row[1],
                                                               defaults={'price': row[3], 'stock': row[2]},
                                                               )
                messages.success(request, "Фикстуры успешно загружены.")
            return redirect('app_store:store_detail', store)
        else:
            return redirect('app_store:store_detail', store)


def handle_uploaded_file(f, name):
    # TODO handle_uploaded_file description
    with open(f'fixtures/{name}.htm', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
