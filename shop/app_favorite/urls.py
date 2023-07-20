from django.urls import path

from app_favorite import views

urlpatterns = [
    path("", views.FavoriteDetailView.as_view(), name="detail_favorites"),
    path("add/<int:pk>/", views.FavoriteAddItem.as_view(), name="add_item"),
    path("remove/<int:pk>/", views.FavoriteRemoveItem.as_view(), name="remove_item"),
]
