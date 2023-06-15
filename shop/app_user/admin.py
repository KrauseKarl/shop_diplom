from django.contrib import admin
from django.utils.safestring import mark_safe

from app_user.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_user_group', 'get_user_group',  'get_phone', 'full_image']
    readonly_fields = ['get_full_name', 'full_image', 'get_phone', 'user']
    fields = (('full_image', 'get_full_name', 'get_phone'), ('telephone','user', 'get_user_group'))

    def get_full_name(self, obj):
        if obj.user:
            return f'{obj.user.first_name} {obj.user.last_name} '

    def get_user_group(self, obj):
        if obj:
            groups = obj.user.groups.first()
            return groups

    def full_image(self, obj):
        if obj.avatar:
            return mark_safe(f'<img style="border-radius:10px;margin:10px" src="{obj.avatar.url}" width=100/>')

    def get_phone(self, obj):
        if obj.telephone:
            t = obj.telephone
            telephone = f'+7 ({t[0:3]}) {t[3:6]} {t[6:8]} {t[8:]}'
            return telephone

    get_user_group.short_description = 'группы'
    full_image.short_description = 'аватар'
    get_phone.short_description = 'телефон'
    get_full_name.short_description = 'ФИО'


admin.site.register(Profile, ProfileAdmin)
