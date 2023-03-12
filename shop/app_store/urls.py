from django.urls import path
from app_store.views import *

app_name = 'app_store'

urlpatterns = [
    path('store/', StoreListView.as_view(), name='store_list'),
    path('store/<int:pk>/', StoreDetailView.as_view(), name='store_detail'),
    path('store/create/', CreateStoreView.as_view(), name='create_store'),
    path('store/<int:pk>/edit/', StoreUpdateViews.as_view(), name='store_edit'),

    path('store/<int:pk>/category/<slug:slug>/', StoreDetailView.as_view(), name='category_item'),
    path('store/<int:pk>/sorted/<slug:order_by>/', StoreDetailView.as_view(), name='item_sorted'),

    path('delivery/', DeliveryListView.as_view(), name='delivery_list'),
    path('delivery/<slug:status>/', DeliveryListView.as_view(), name='delivery_progress'),
    path('delivery/detail/<int:pk>/', DeliveryDetailView.as_view(), name='delivery_detail'),
    path('delivery/detail/<int:pk>/edit/', DeliveryUpdateView.as_view(), name='delivery_edit'),
    path('delivery/cart_item/<int:pk>/edit/', CartItemUpdateView.as_view(), name='cart_item_edit'),
    path('delivery/detail/<int:order_id>/sent/', SentPurchase.as_view(), name='sent_purchase'),

    path('comment/list/', CommentListView.as_view(), name='comment_list'),
    path('comment/<int:pk>/moderate/<slug:slug>/', CommentModerate.as_view(), name='comment_moderate'),

    path('item/add/<int:pk>/store/', CreateItemView.as_view(), name='add_item'),
    path('item/edit/<int:pk>/', UpdateItemView.as_view(), name='edit_item'),
    path('item/delete/<int:item_id>/', DeleteItem.as_view(), name='delete_item'),

    path('category/list/', CategoryListView.as_view(), name='category_list'),
    path('category/detail/<slug:slug>/feature/list/', FeatureListView.as_view(), name='feature_list'),
    path('category/create/', CategoryCreateView.as_view(), name='create_category'),
    path('feature/create/', CreateFeatureView.as_view(), name='feature_create'),
    path('feature_value/create/', CreateFeatureValueView.as_view(), name='feature_value_create'),


    path('tag/list/', TagListView.as_view(), name='tag_list'),
    path('tag/create/', CreateTagView.as_view(), name='create_tag'),
    path('tag/add/<int:pk>/', AddTagView.as_view(), name='add_tag'),
    path('tag/delete/<int:item_id>/tag/<int:tag_id>/', DeleteTag.as_view(), name='delete_tag'),



    path('image/delete/<int:item_id>/image/<int:image_id>/', DeleteImage.as_view(), name='delete_image'),

    path('export_data_csv/<int:pk>/', export_data_to_csv, name='export_data'),
    path('import_data_from_cvs/<int:pk>', import_data_from_cvs, name='import_data'),

]


