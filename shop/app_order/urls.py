from django.urls import path

from app_order.views import (
    OrderCreate,
    SuccessOrdered,
    FailedOrdered,
    OrderList,
    OrderDetail,
    PaymentCardView,
    PaymentAccountView,
    SuccessPaid,
    ConfirmReceiptPurchase,
    InvoicesList,
    PaymentProgress,
    RejectOrder
)
app_name = 'app_order'

urlpatterns = [
    path('order_create/', OrderCreate.as_view(), name='order_create'),
    path('order_list/', OrderList.as_view(), name='order_list'),
    path('order_list/<slug:status>/', OrderList.as_view(), name='order_progress'),

    path('invoices_list/', InvoicesList.as_view(), name='invoices_list'),
    path('invoices_list/<slug:sort>/', InvoicesList.as_view(), name='invoices_by_date'),

    path('order_detail/<int:pk>/', OrderDetail.as_view(), name='order_detail'),
    path('order_detail/<int:order_id>/confirm/', ConfirmReceiptPurchase.as_view(), name='order_confirm'),
    path('order_list/<int:order_id>/cancel/', RejectOrder.as_view(), name='order_cancel'),
    path('success_order/', SuccessOrdered.as_view(), name='success_order'),
    path('failed_order/', FailedOrdered.as_view(), name='failed_order'),

    path('payment_progress/', PaymentProgress.as_view(), name='progress_payment'),
    path('pay_by_card/', PaymentCardView.as_view(), name='pay_by_card'),
    path('pay_by_account/', PaymentAccountView.as_view(), name='pay_by_account'),
    path('success_pay/', SuccessPaid.as_view(), name='success_pay'),
]
