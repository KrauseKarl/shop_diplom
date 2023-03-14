from django.contrib import admin
from app_order.models import Order


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'created', 'status', 'total_sum',
                    'delivery', 'pay', ]
    list_filter = ('is_paid', 'status', 'store')


admin.site.register(Order, OrderAdmin)
