from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("phone_number", "name", "role", "is_phone_verified", "created_at")
    list_filter = ("role", "is_phone_verified", "is_active")
    search_fields = ("phone_number", "name", "uuid")
    ordering = ("-created_at",)
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Profile", {"fields": ("name", "uuid", "role", "is_phone_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ("uuid", "created_at", "updated_at")
