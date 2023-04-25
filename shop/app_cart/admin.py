from django.contrib import admin

from app_cart.models import Cart, CartItem


class OrderItemInline(admin.StackedInline):
    model = Cart.items.through
    extra = 1


class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'quantity', 'user', 'is_paid']
    list_filter = ('user', 'is_paid',)


class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_anonymous', 'created', 'session_key']
    list_filter = ('user', 'is_anonymous', 'session_key', )
    inlines = [OrderItemInline, ]
    readonly_fields = ['user', 'is_anonymous', 'session_key']
    exclude = ['items', ]


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
