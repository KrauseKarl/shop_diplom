"""Модуль содержит URL-адреса для работы с пользователем."""
from django.urls import path
from app_user import views

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.CreateProfile.as_view(), name="register"),
    path("register_order/", views.CreateProfileOrder.as_view(), name="register_order"),
    path("block/", views.BlockView.as_view(), name="block_page"),
    path("account/<int:pk>/", views.DetailAccount.as_view(), name="account"),
    path("history/<int:pk>/", views.HistoryDetailView.as_view(), name="history_view"),
    path("prof/<int:pk>/", views.DetailProfile.as_view(), name="profile"),
    path("prof/<int:pk>/comments", views.CommentList.as_view(), name="comment_list"),
    path("prof/<int:pk>/edit/", views.UpdateProfile.as_view(), name="profile_edit"),

    path("pass_change/", views.PasswordChange.as_view(),
         name="password_change"),
    path("pass_change_done/", views.PasswordChangeDone.as_view(),
         name="password_change_done"),
    path("pass_reset_complete/", views.PasswordResetComplete.as_view(),
         name="password_reset_complete"),
    path("pass_reset/", views.PasswordReset.as_view(),
         name="password_reset"),
    path("pass_reset/done/", views.PasswordResetDone.as_view(),
         name="password_reset_done"),
    path("pass_reset_confirm/<uidb64>/<token>", views.PasswordResetConfirm.as_view(),
         name="password_reset_confirm", ),
]
