from django.contrib import admin

from app_invoice.models import Invoice


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id',
                    'order',
                    'number',
                    'created',
                    'total_purchase_sum',
                    'delivery_cost',
                    'total_sum' ]


admin.site.register(Invoice, InvoiceAdmin)
