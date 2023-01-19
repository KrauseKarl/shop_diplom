from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.urls import path
from app_user.views import *

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('register/', CreateProfile.as_view(), name='register'),
    path('account/<int:pk>/', DetailAccount.as_view(), name='account'),
    path('profile/<int:pk>/', DetailProfile.as_view(), name='profile'),
    path('profile/<int:pk>/comment_list', CommentList.as_view(), name='comment_list'),
    path('profile/<int:pk>/edit/', UpdateProfile.as_view(), name='profile_edit'),
    path('history_view/<int:pk>/', DetailHistoryView.as_view(), name='history_view'),
    path('profile_edit/<int:pk>/', UpdateProfile.as_view(), name='profile_edit'),
    path("activate/<slug:uidb64>/<slug:token>/", account_activate, name="activate"),
    path("activate/account_activated/", ActivatedAccount.as_view(), name="activated_success"),
    path("activate/invalid_activation/", InvalidActivatedAccount.as_view(), name="invalid_activation"),

    path('password_change/', PasswordChange.as_view(), name='password_change'),
    path('password_change_done/', PasswordChangeDone.as_view(), name='password_change_done'),
    path('password_reset_complete/', PasswordResetComplete.as_view(), name='password_reset_complete'),
    path('password_reset/', PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>', PasswordResetConfirm.as_view(),
         name="password_reset_confirm"),


]


