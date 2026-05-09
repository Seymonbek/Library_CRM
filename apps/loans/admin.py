from  django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Loans, Fines, Waitlists, Notifications, SystemLogs, LibrarySettings

@admin.register(Loans)
class LoansAdmin(ModelAdmin):
    list_display = ["id", "user", "copy", "status", "due_date", "is_overdue"]
    list_filter = ["status", "due_date"]
    search_fields = ["user__phone_number", "copy__inventory_number"]
    readonly_fields = ["created_at"]

@admin.register(Fines)
class FinesAdmin(ModelAdmin):
    list_display = ["loan", "amount", "reason", "is_paid", "paid_at"]
    list_filter = ["is_paid", "reason"]
    search_fields = ["loan__user__phone_number"]

@admin.register(Waitlists)
class WaitlistsAdmin(ModelAdmin):
    list_display = ["user", "book", "status", "created_at"]
    list_filter = ["status"]

@admin.register(SystemLogs)
class SystemLogsAdmin(ModelAdmin):
    list_display = ["admin", "action", "target_type", "created_at"]
    list_filter = ["action", "target_type"]
    search_fields = ["admin", "action", "target", "target_type", "details", "created_at"]

    # Loglarni o'chirib bo'lmaydigan qilish
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(LibrarySettings)
class LibrarySettingsAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not LibrarySettings.objects.exists()

@admin.register(Notifications)
class NotificationsAdmin(ModelAdmin):
    list_display = ["user", "type", "is_sent", "sent_at"]