from django.contrib import admin
from django.utils.safestring import mark_safe
from app_item.forms import ItemForm
from app_store.models import Store
from app_item.models import Item, Category, Tag, Comment, Image, Feature, FeatureValue

EMPTY_VALUE = 'незаполнен'
BLANK_CHOICE_DASH = [("", "выберите действие")]


class ItemTagsInline(admin.TabularInline):
    model = Item.tag.through
    raw_id_fields = ['tag', ]
    extra = 1


class ItemFeatureInline(admin.TabularInline):
    model = Item.feature_value.through
    extra = 3


class ItemImageInline(admin.TabularInline):
    model = Item.images.through
    # raw_id_fields = ['image', ]
    extra = 1


class ItemAdmin(admin.ModelAdmin):
    form = ItemForm
    fields = (
        ('title', 'slug'), ('price', 'stock', 'is_available', 'limited_edition'),
        ('category', 'store'), 'color')
    list_display = ['title', 'category', 'store', 'price', 'stock', 'set_colors']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ItemImageInline, ItemTagsInline, ItemFeatureInline ]
    radio_fields = {'color': admin.VERTICAL}
    list_filter = ('is_available', 'limited_edition', 'category', 'store')
    raw_id_fields = ['category', 'tag']
    empty_value_display = EMPTY_VALUE

    # def full_image(self, obj):
    #     return mark_safe(f'<img src="{obj.image.url}" width=80/>')

    # full_image.short_description = "изображение"
    # full_image.allow_tags = True

    def set_colors(self, obj):
        if obj.color:
            return mark_safe(f'<div style="background-color:{obj.color}; box-shadow: 0 0 2px; padding: 20px"></div>')
        return mark_safe(f'<div>не определен </div>')

    set_colors.short_description = "цвет товара"

    def get_action_choices(self, request, default_choices=None):
        if default_choices is None:
            default_choices = BLANK_CHOICE_DASH
        return super().get_action_choices(request, default_choices)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent_category', 'description']
    prepopulated_fields = {'slug': ('title',)}
    empty_value_display = EMPTY_VALUE


class TagAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ItemTagsInline, ]
    empty_value_display = EMPTY_VALUE


class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'review']
    empty_value_display = EMPTY_VALUE


class ImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'updated', 'image')


class FeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'widget_type', 'is_active']
    prepopulated_fields = {'slug': ('title',)}
    empty_value_display = EMPTY_VALUE


class FeatureValueAdmin(admin.ModelAdmin):
    list_display = ['feature', 'value', ]
    empty_value_display = EMPTY_VALUE


admin.site.register(Item, ItemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(FeatureValue, FeatureValueAdmin)
