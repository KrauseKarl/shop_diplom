from django.urls import path

from app_order import views


app_name = 'app_order'

urlpatterns = [
    path('order_create/', views.OrderCreate.as_view(), name='order_create'),
    path('order_list/', views.OrderList.as_view(), name='order_list'),
    path('order_list/<slug:status>/', views.OrderList.as_view(), name='order_progress'),


    path('order_detail/<int:pk>/', views.OrderDetail.as_view(), name='order_detail'),
    path('order_update/<int:pk>/update/', views.OrderUpdatePayWay.as_view(), name='order_update'),
    path('order_detail/<int:pk>/confirm/', views.ConfirmReceiptPurchase.as_view(), name='order_confirm'),
    path('order_list/<int:pk>/cancel/', views.OrderCancel.as_view(), name='order_cancel'),
    path('success_order/', views.SuccessOrdered.as_view(), name='success_order'),
    path('failed_order/', views.FailedOrdered.as_view(), name='failed_order'),

    path('progress_payment/<int:pk>/', views.PaymentView.as_view(), name='progress_payment'),
    path("pay_order/", views.pay_order, name="pay_order"),
    path("get_status_payment/<int:order_id>/<task_id>/", views.get_status_payment, name="get_status_payment"),
    path('success_pay/<int:order_id>/', views.SuccessPaid.as_view(), name='success_pay'),
    path('failed_pay/<int:order_id>/', views.FailedPaid.as_view(), name='failed_pay'),
]
