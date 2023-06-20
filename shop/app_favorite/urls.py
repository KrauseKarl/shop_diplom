from django.urls import path

from app_favorite import views

urlpatterns = [
    path('', views.FavoriteDetailView.as_view(), name='detail_favorites'),
    path('compare/', views.CompareView.as_view(), name='compare'),
    path('add/<int:pk>/', views.FavoriteAddFlat.as_view(), name='add'),
    path('remove/<int:pk>/', views.FavoriteRemoveFlat.as_view(), name='remove'),
    path('remove/', views.FavoriteRemoveAll.as_view(), name='remove_all'),
]
