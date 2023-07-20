"""Модуль содержит URL-адреса для работы с корзиной."""

from django.urls import path
from app_cart import views

app_name = "app_cart"

urlpatterns = [
    path("<int:pk>/detail/", views.CartDetail.as_view(), name="cart"),
    path("cart_create/", views.CreateCart.as_view(), name="cart_create"),
    path("add/<int:pk>/", views.AddItemToCart.as_view(), name="add_cart"),
    path(
        "update/<int:pk>/item/<int:item_id>/",
        views.UpdateCountItem.as_view(),
        name="update",
    ),
    path(
        "remove/<int:pk>/",
        views.RemoveItemFromCart.as_view(),
        name="remove_cart",
    ),
]
