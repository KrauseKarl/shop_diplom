"""Модуль содержит URL-адреса для работы с магазинами."""
from django.urls import path
from app_store import views

app_name = "app_store"

urlpatterns = [
    path("seller/dashboard/", views.SellerDashBoard.as_view(), name="dashboard"),

    path("store/", views.StoreList.as_view(), name="store_list"),
    path("store/<int:pk>/", views.StoreDetail.as_view(), name="store_detail"),
    path("store/create/", views.StoreCreate.as_view(), name="create_store"),
    path("store/<int:pk>/edit/", views.StoreUpdate.as_view(), name="store_edit"),
    path("store/<int:pk>/category/<slug:slug>/", views.StoreDetail.as_view(), name="category_item"),
    path("store/<int:pk>/sorted/<slug:order_by>/", views.StoreDetail.as_view(), name="item_sorted"),

    path("item/add/<int:pk>/", views.ItemCreate.as_view(), name="add_item"),
    path("item/edit/<int:pk>/", views.ItemUpdate.as_view(), name="edit_item"),
    path("item/delete/<int:pk>/", views.ItemDelete.as_view(), name="delete_item"),

    path("delivery/", views.DeliveryList.as_view(), name="delivery_list"),
    path("delivery/<slug:status>/", views.DeliveryList.as_view(), name="delivery_progress"),
    path("delivery/detail/<int:pk>/", views.DeliveryDetail.as_view(), name="delivery_detail"),
    path("delivery/detail/<int:pk>/edit/", views.DeliveryUpdate.as_view(), name="delivery_edit"),
    path("delivery/item/<int:pk>/edit/", views.OrderItemUpdate.as_view(), name="order_item_edit"),
    path("delivery/sent/<int:pk>/", views.SentPurchase.as_view(), name="sent_purchase"),

    path("comment/list/", views.CommentList.as_view(), name="comment_list"),
    path("comment/<int:pk>/", views.CommentDetail.as_view(), name="comment_detail"),

    path("value/<slug:slug>/item/<int:pk>/del/", views.RemoveValue.as_view(), name="value_del"),
    #
    path("tag/list/", views.TagList.as_view(), name="tag_list"),
    path("tag/add/<int:pk>/", views.AddTag.as_view(), name="add_tag"),
    path("tag/<int:tag_id>/itm/<int:item_id>/del/", views.RemoveTag.as_view(), name="delete_tag"),

    path("image/<int:pk>/del/", views.DeleteImage.as_view(), name="delete_image"),
    path("image/<int:pk>/update/", views.MakeImageAsMain.as_view(), name="make_image_main"),

    path("export_data/<int:pk>/", views.export_data_to_csv, name="export_data"),
    path("import_data/<int:pk>", views.import_data_from_cvs, name="import_data"),
]
