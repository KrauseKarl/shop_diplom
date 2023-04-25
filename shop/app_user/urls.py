from django.urls import path
from app_user import views

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.CreateProfile.as_view(), name='register'),

    path('account/<int:pk>/', views.DetailAccount.as_view(), name='account'),
    path('history_view/<int:pk>/', views.HistoryDetailView.as_view(), name='history_view'),
    path('profile/<int:pk>/', views.DetailProfile.as_view(), name='profile'),
    path('profile/<int:pk>/comment_list', views.CommentList.as_view(), name='comment_list'),
    path('profile/<int:pk>/edit/', views.UpdateProfile.as_view(), name='profile_edit'),
    path('profile_edit/<int:pk>/', views.UpdateProfile.as_view(), name='profile_edit'),

    path("activate/<slug:uidb64>/<slug:token>/", views.account_activate, name="activate"),
    path("activate/account_activated/", views.ActivatedAccount.as_view(), name="activated_success"),
    path("activate/invalid_activation/", views.InvalidActivatedAccount.as_view(), name="invalid_activation"),

    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change_done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    path('password_reset_complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>', views.PasswordResetConfirm.as_view(),
         name="password_reset_confirm"),


]


