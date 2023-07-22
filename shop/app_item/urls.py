"""Модуль содержит URL-адреса для работы с каталогом товаров."""
from django.urls import path
from app_item import views

app_name = "app_item"


urlpatterns = [
    path(
        "list/best_seller",
        views.ItemBestSellerList.as_view(),
        name="item_best_seller",
    ),
    path("list/new", views.ItemNewList.as_view(), name="item_new"),
    path("list/for_you", views.ItemForYouList.as_view(), name="item_for_you"),
    path("list/search/", views.FilterListView.as_view(), name="search"),
    path("list/filter/", views.FilterListView.as_view(), name="filter"),
    path(
        "list/category/<slug:category>/",
        views.CategoryListView.as_view(),
        name="item_category",
    ),
    path("list/tag/<slug:tag>/", views.TagListView.as_view(), name="item_tag"),
    path(
        "list/store/<slug:slug>/",
        views.StoreItemList.as_view(),
        name="store_list",
    ),
    path(
        "list/remove_param/<slug:param>/",
        views.remove_param,
        name="remove_param",
    ),
    path("detail/<int:pk>/", views.ItemDetail.as_view(), name="item_detail"),
    path(
        "detail/<int:pk>/delete/comment/<int:comment_id>/",
        views.DeleteComment.as_view(),
        name="comment_delete",
    ),
    path(
        "detail/<int:pk>/edit/comment/<int:comment_id>/",
        views.EditComment.as_view(),
        name="comment_edit",
    ),
]
