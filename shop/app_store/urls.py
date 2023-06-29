from django.urls import path
from app_store import views

app_name = 'app_store'

urlpatterns = [
    path('seller/dashboard/', views.SellerDashBoardView.as_view(), name='dashboard'),
    path('store/', views.StoreListView.as_view(), name='store_list'),
    path('store/<int:pk>/', views.StoreDetailView.as_view(), name='store_detail'),
    path('store/create/', views.StoreCreateView.as_view(), name='create_store'),
    path('store/<int:pk>/edit/', views.StoreUpdateViews.as_view(), name='store_edit'),

    path('store/<int:pk>/category/<slug:slug>/', views.StoreDetailView.as_view(), name='category_item'),
    path('store/<int:pk>/sorted/<slug:order_by>/', views.StoreDetailView.as_view(), name='item_sorted'),

    path('item/add/<int:pk>/', views.ItemCreateView.as_view(), name='add_item'),
    path('item/edit/<int:pk>/', views.ItemUpdateView.as_view(), name='edit_item'),
    path('item/delete/<int:item_id>/', views.ItemDeleteView.as_view(), name='delete_item'),

    path('delivery/', views.DeliveryListView.as_view(), name='delivery_list'),
    path('delivery/<slug:status>/', views.DeliveryListView.as_view(), name='delivery_progress'),
    path('delivery/detail/<int:pk>/', views.DeliveryDetailView.as_view(), name='delivery_detail'),
    path('delivery/detail/<int:pk>/edit/', views.DeliveryUpdateView.as_view(), name='delivery_edit'),
    path('delivery/order_item/<int:pk>/edit/', views.OrderItemUpdateView.as_view(), name='order_item_edit'),
    path('delivery/detail/<int:order_id>/sent/', views.SentPurchase.as_view(), name='sent_purchase'),

    path('comment/list/', views.CommentListView.as_view(), name='comment_list'),
    path('comment/<int:pk>/', views.CommentDetail.as_view(), name='comment_detail'),
    # path('comment/<int:pk>/update/', CommentModerate.as_view(), name='comment_update'),
    # path('comment/<int:pk>/delete/', CommentDelete.as_view(), name='comment_delete'),

    # path('category/store/<int:pk>/list/', CategoryListView.as_view(), name='category_list'),
    # path('category/detail/<slug:slug>/feature/list/', FeatureListView.as_view(), name='feature_list'),
    # path('category/create/store/<int:pk>', CategoryCreateView.as_view(), name='create_category'),
    #
    # path('feature/<int:pk>/list/', FeatureListView.as_view(), name='feature_list'),
    # path('feature/create/<int:pk>/', CreateFeatureView.as_view(), name='feature_create'),
    # path('feature/value/<int:pk>/create/', CreateFeatureValueView.as_view(), name='feature_value_create'),
    # path('feature/<slug:slug>/item/<int:pk>/remove/', RemoveFeatureValueView.as_view(), name='value_remove'),
    #
    # path('tag/list/', TagListView.as_view(), name='tag_list'),
    # path('tag/create/', CreateTagView.as_view(), name='create_tag'),
    # path('tag/add/<int:pk>/', AddTagToItem.as_view(), name='add_tag'),
    # path('tag/delete/<int:item_id>/tag/<int:tag_id>/', RemoveTagFromItem.as_view(), name='delete_tag'),

    path('image/delete/<int:pk>/image/', views.DeleteImage.as_view(), name='delete_image'),
    path('image/update/<int:pk>/image/', views.MakeImageAsMain.as_view(), name='make_image_main'),

    path('export_data_csv/<int:pk>/', views.export_data_to_csv, name='export_data'),
    path('import_data_from_cvs/<int:pk>', views.import_data_from_cvs, name='import_data'),

]


