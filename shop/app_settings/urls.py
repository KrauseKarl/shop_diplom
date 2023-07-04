from django.urls import path

from app_settings import views

app_name = 'app_settings'
urlpatterns = [
    path('admin/dashboard/', views.AdminDashBoardView.as_view(), name='dashboard'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('edit/<int:pk>/', views.SettingsUpdatedView.as_view(), name='settings_edit'),

    path('customer/list/', views.CustomerListView.as_view(), name='customer_list'),
    path('customer/<int:pk>/update/', views.CustomerDeleteView.as_view(), name='customer_update_status'),

    path('seller/list/', views.SellerListView.as_view(), name='seller_list'),
    path('seller/<int:pk>/update/', views.SellerDeleteView.as_view(), name='seller_update_status'),

    path('store/list/', views.StoreListView.as_view(), name='store_list'),
    path('product/list/', views.ProductListView.as_view(), name='product_list'),

    path('comments/list/', views.CommentListView.as_view(), name='comments_list'),
    path('comment/<int:pk>/detail/', views.CommentDetail.as_view(), name='comment_detail'),
    path('comment/<int:pk>/update/', views.CommentModerate.as_view(), name='comment_update'),
    path('comment/<int:pk>/delete/', views.CommentDelete.as_view(), name='comment_delete'),

    path('category/list/', views.CategoryListView.as_view(), name='category_list'),
    path('category/create/', views.CategoryCreateView.as_view(), name='create_category'),
    path('category/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('category/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    path('tag/list/', views.TagListView.as_view(), name='tag_list'),
    path('tag/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tag/<int:pk>/edit/', views.TagUpdateView.as_view(), name='tag_edit'),
    path('tag/<int:pk>/delete/', views.TagDeleteView.as_view(), name='tag_delete'),

    path('feature/list/<int:pk>/', views.FeatureListView.as_view(), name='feature_list'),
    path('feature/create/<int:pk>/', views.FeatureCreateView.as_view(), name='feature_create'),
    path('feature/edit/<int:category_id>/feature/<int:pk>/', views.FeatureUpdateView.as_view(), name='feature_edit'),
    path('feature/delete/<int:category_id>/feature/<int:pk>/', views.FeatureDeleteView.as_view(), name='feature_delete'),

    path('feature/value/<int:pk>/create/', views.ValueCreateView.as_view(), name='value_create'),
    path('feature/delete/<int:category_id>/value/<int:pk>/', views.ValueDeleteView.as_view(), name='value_delete'),
    path('order/list/', views.OrderListView.as_view(), name='admin_order_list'),
    path('order/<int:pk>/detail/', views.OrderDetailView.as_view(), name='admin_order_detail'),


]

