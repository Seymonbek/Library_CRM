from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ["id", "username", "phone_number", "role", "status", "balance", "is_active"]
    list_filter = ["role", "status", "is_active"]
    search_fields = ["username", "phone_number", "first_name", "last_name", "telegram_id"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Shaxsiy ma'lumotlar", {"fields": ("first_name", "last_name", "phone_number", "telegram_id", "balance")}),
        ("Huquqlar", {"fields": ("role", "status", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Muhim sanalar", {"fields": ("last_login", "date_joined")}),
    )