from django.contrib import admin
from django.utils.safestring import mark_safe

from app_store.models import Store


class StoreAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'full_image', 'delivery_fees', 'min_free_delivery']
    readonly_fields = ['full_image', 'owner']

    # fields = ('title', 'owner', ('logo', 'full_image'), 'is_active')

    def full_image(self, obj):
        return mark_safe(f'<img src="{obj.logo.url}" width=80/>')


admin.site.register(Store, StoreAdmin)
