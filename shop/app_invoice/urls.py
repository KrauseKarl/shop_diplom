"""Модуль содержит URL-адреса для работы с чека оплаты и адресами."""
from django.urls import path

from app_invoice import views

app_name = "app_invoice"

urlpatterns = [
    path("invoices_list/", views.InvoicesList.as_view(), name="invoices_list"),
    path(
        "invoices_detail/<int:pk>/",
        views.InvoicesDetail.as_view(),
        name="invoices_detail",
    ),
    path(
        "invoices_list/<slug:sort>/",
        views.InvoicesList.as_view(),
        name="invoices_by_date",
    ),
    path("address/list/", views.AddressList.as_view(), name="address_list"),
    path(
        "address/create/", views.AddressCreate.as_view(), name="address_create"
    ),
    path(
        "address/edit/<int:pk>/",
        views.AddressUpdate.as_view(),
        name="address_edit",
    ),
    path(
        "address/remove/<int:pk>/",
        views.AddressDelete.as_view(),
        name="address_remove",
    ),
]
