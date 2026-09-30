"""
accounts/urls.py
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, LogoutView, RegisterView, ProfileView, UserListView, UserDetailView

urlpatterns = [
    path('login/',          LoginView.as_view(),       name='auth-login'),
    path('logout/',         LogoutView.as_view(),      name='auth-logout'),
    path('refresh/',        TokenRefreshView.as_view(), name='auth-refresh'),
    path('register/',       RegisterView.as_view(),    name='auth-register'),
    path('profile/',        ProfileView.as_view(),     name='auth-profile'),
    path('users/',          UserListView.as_view(),    name='auth-users-list'),
    path('users/<uuid:pk>/', UserDetailView.as_view(), name='auth-user-detail'),
]
