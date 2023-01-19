from django.urls import path
from app_cart.views import CartDetail, AddItemToCart, RemoveItemFromCart, UpdateCountItemFromCart, CreateCart

app_name = 'app_cart'

urlpatterns = [
    path('<int:pk>/detail/', CartDetail.as_view(), name='cart'),
    path('cart_create/', CreateCart.as_view(), name='cart_create'),
    path('add/<int:pk>/', AddItemToCart.as_view(), name='add_cart'),
    path('update/<int:pk>/item/<int:item_id>/', UpdateCountItemFromCart.as_view(), name='update'),
    path('remove/<int:pk>/', RemoveItemFromCart.as_view(), name='remove_cart'),

]
