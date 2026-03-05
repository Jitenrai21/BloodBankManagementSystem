from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'role', 'is_active', 'is_approved', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_approved', 'is_staff')
    search_fields = ('email', 'phone')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('phone',)}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_approved', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )
    readonly_fields = ('date_joined', 'last_login')
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'role', 'password1', 'password2')}),
    )

