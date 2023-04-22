from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.defaults import permission_denied, page_not_found, server_error
from shop.views import MainPage, page_not_found


handler403 = 'shop.views.my_permission_denied'
handler404 = 'shop.views.my_page_not_found'
handler500 = 'shop.views.my_server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MainPage.as_view(), name='main_page'),
    path('accounts/', include(('app_user.urls', 'app_user'), namespace='app_user')),
    path('cart/', include(('app_cart.urls', 'app_cart'), namespace='app_cart')),
    path('order/', include(('app_order.urls', 'app_order'), namespace='app_order')),
    path('store/', include(('app_store.urls', 'app_store'), namespace='app_store')),
    path('item/', include(('app_item.urls', 'app_item'), namespace='app_item')),
    path('invoice/', include(('app_invoice.urls', 'app_invoice'), namespace='app_invoice')),
    path('settings/', include(('app_settings.urls', 'app_settings'), namespace='app_settings')),
    path('__debug__/', include('debug_toolbar.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# handler400 = bad_request
