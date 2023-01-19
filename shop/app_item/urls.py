from django.urls import path
from app_item.views import *

app_name = 'app_item'

urlpatterns = [
    path('list/', ItemList.as_view(), name='item_list'),
    path('list/best_seller', ItemBestSellerList.as_view(), name='item_best_seller'),
    path('list/new', ItemNewList.as_view(), name='item_new'),

    path('list/search/', ItemList.as_view(), name='search'),
    path('list/filter/', FilterListView.as_view(), name='filter'),
    path('list/tag/<slug:tag>/', ItemList.as_view(), name='item_tag'),
    path('list/category/<slug:category>/', ItemList.as_view(), name='item_category'),
    path('list/remove_param/<slug:param>/', remove_param, name='remove_param'),

    path('detail/<int:pk>/', ItemDetail.as_view(), name='item_detail'),
    path('detail/<int:pk>/delete/comment/<int:comment_id>/', DeleteComment.as_view(), name='comment_delete'),
    path('detail/<int:pk>/edit/comment/<int:comment_id>/', EditComment.as_view(), name='comment_edit'),
]
