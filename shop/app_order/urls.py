from django.urls import path

from app_order.views import *


app_name = 'app_order'

urlpatterns = [
    path('order_create/', OrderCreate.as_view(), name='order_create'),
    path('order_list/', OrderList.as_view(), name='order_list'),
    path('order_list/<slug:status>/', OrderList.as_view(), name='order_progress'),

    path('address/create/', AddressCreate.as_view(), name='address_create'),
    path('address/list/', AddressList.as_view(), name='address_list'),
    path('address/edit/<int:pk>/', AddressUpdate.as_view(), name='address_edit'),
    path('address/remove/<int:pk>/', AddressDelete.as_view(), name='address_remove'),


    path('order_detail/<int:pk>/', OrderDetail.as_view(), name='order_detail'),
    path('order_detail/<int:order_id>/confirm/', ConfirmReceiptPurchase.as_view(), name='order_confirm'),
    path('order_list/<int:order_id>/cancel/', RejectOrder.as_view(), name='order_cancel'),
    path('success_order/', SuccessOrdered.as_view(), name='success_order'),
    path('failed_order/', FailedOrdered.as_view(), name='failed_order'),

    path('progress_payment/<int:pk>/', PaymentView.as_view(), name='progress_payment'),
    path("validate_username/", validate_username, name="validate_username"),
    path("get_status_payment/<int:order_id>/<task_id>/", get_status_payment, name="get_status_payment"),
    path('success_pay/<int:order_id>/', SuccessPaid.as_view(), name='success_pay'),
    path('failed_pay/<int:order_id>/', FailedPaid.as_view(), name='failed_pay'),
]
