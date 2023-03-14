from django.urls import path

from app_invoice.views import *

app_name = 'app_invoice'

urlpatterns = [
    path('invoices_list/', InvoicesList.as_view(), name='invoices_list'),
    path('invoices_detail/<int:pk>/', InvoicesDetail.as_view(), name='invoices_detail'),
    path('invoices_list/<slug:sort>/', InvoicesList.as_view(), name='invoices_by_date'),
]
