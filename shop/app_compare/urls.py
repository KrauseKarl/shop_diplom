from django.urls import path

from app_compare import views

urlpatterns = [
    path('', views.CompareItemView.as_view(), name='compare'),
    path('add/<int:pk>/', views.AddItemComparison.as_view(), name='add_item'),
    path('remove/<int:pk>/', views.RemoveItemComparison.as_view(), name='remove_item'),
    path('clear_compare_list/', views.RemoveAllComparison.as_view(), name='clear_compare_list'),
]
