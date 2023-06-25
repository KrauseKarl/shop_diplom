from django.urls import path

from app_favorite import views

urlpatterns = [
    path('', views.FavoriteDetailView.as_view(), name='detail_favorites'),
    path('compare/', views.CompareItemView.as_view(), name='compare_items'),
    path('add/<int:pk>/', views.FavoriteAddItem.as_view(), name='add_item'),
    path('remove/<int:pk>/', views.FavoriteRemoveItem.as_view(), name='remove_item'),
    path('clear_favorites/', views.FavoriteRemoveAll.as_view(), name='clear_favorites'),
]
