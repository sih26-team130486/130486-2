"""
accounts/admin.py — Register CustomUser in Django Admin
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display  = ['username', 'email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['username', 'email', 'full_name']
    ordering      = ['-created_at']

    fieldsets = (
        (None,          {'fields': ('username', 'password')}),
        ('Personal',    {'fields': ('email', 'full_name')}),
        ('Role & Access', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ['created_at', 'updated_at']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )
