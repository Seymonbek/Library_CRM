from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError
from unfold.admin import ModelAdmin

from apps.loans.services import approve_loan_request
from .models import Loans, Fines, Waitlists, Notifications, SystemLogs, LibrarySettings



@admin.register(Loans)
class LoanAdmin(ModelAdmin):
    list_display = ["id", "user", "copy", "status", "requested_days", "due_date", "issued_by"]
    list_filter = ["status", "due_date"]
    search_fields = ["user__phone_number", "copy__inventory_number", "copy__book__title"]
    readonly_fields = ["created_at"]
    actions = ["issue_book_action"]

    @admin.action(description="Tanlangan pending so'rovlarni tasdiqlash")
    def issue_book_action(self, request, queryset):
        pending_loans = queryset.filter(status=Loans.Status.PENDING).select_related("copy", "copy__book", "user")

        if not pending_loans.exists():
            self.message_user(request, "Hech qanday kutilayotgan so'rov tanlanmadi.", messages.WARNING)
            return

        success_count = 0
        error_messages = []

        for loan in pending_loans:
            try:
                approve_loan_request(loan=loan, actor=request.user)
                success_count += 1
            except ValidationError as e:
                detail = e.detail if hasattr(e, 'detail') else str(e)
                error_messages.append(f"Loan #{loan.pk}: {detail}")

        if success_count:
            self.message_user(request, f"{success_count} ta loan muvaffaqiyatli tasdiqlandi.", messages.SUCCESS)

        for err in error_messages:
            self.message_user(request, err, messages.ERROR)

        
@admin.register(Fines)
class FinesAdmin(ModelAdmin):
    list_display = ["loan", "amount", "reason", "is_paid", "paid_at"]
    list_filter = ["is_paid", "reason"]
    search_fields = ["loan__user__phone_number", "loan__copy__book__title"]

@admin.register(Waitlists)
class WaitlistsAdmin(ModelAdmin):
    list_display = ["user", "book", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__phone_number", "book__title"]

@admin.register(SystemLogs)
class SystemLogsAdmin(ModelAdmin):
    list_display = ["admin", "action", "target_type", "created_at"]
    list_filter = ["action", "target_type"]
    search_fields = ["admin__username", "details", "target"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(LibrarySettings)
class LibrarySettingsAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not LibrarySettings.objects.exists()

@admin.register(Notifications)
class NotificationsAdmin(ModelAdmin):
    list_display = ["user", "type", "is_sent", "sent_at", "created_at"]
    list_filter = ["type", "is_sent"]
    search_fields = ["user__phone_number", "message"]