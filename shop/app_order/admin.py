from django.contrib import admin
from app_order.models import Order, Invoice


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'store', 'created', 'status', 'total_sum',
                    'delivery', 'pay', ]
    list_filter = ('is_paid', 'status', 'store')


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'number', 'created', ]


admin.site.register(Order, OrderAdmin)
admin.site.register(Invoice, InvoiceAdmin)
