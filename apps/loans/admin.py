from datetime import timezone, timedelta

from  django.contrib import admin, messages
# from django.contrib.messages import WARNING
from unfold.admin import ModelAdmin
from .models import Loans, Fines, Waitlists, Notifications, SystemLogs, LibrarySettings
from .utils import perform_logging
from ..books.models import BookCopies


@admin.register(Loans)
class LoanAdmin(ModelAdmin):
    list_display = ["id", "user", "copy", "status", "requested_days", "due_date", "issued_by"]
    list_filter = ["status", "due_date"]
    search_fields = ["user__phone_number", "copy__inventory_number"]
    readonly_fields = ["created_at"]
    actions = ["issue_book_action"]

    @admin.action(description="Tanlangan kitoblarni o'quvchiga topshirish (Tasdiqlash)")
    def issue_book_action(self, request, queryset):
        """
        Kutubxonachi tugmani bosganida ishlaydi.
        """
        pending_loans = queryset.filter(status=Loans.Status.PENDING)

        if not pending_loans.exists():
            self.message_user(request, "Hech qanday kutilayotgan so'rov tanlanmadi.")
            return

        count = 0
        for loan in pending_loans:
            # 1. Muddatni hisoblaymiz: Bugun + foydalanuvchi so'ragan kunlar
            today = timezone.now().date()
            loan.due_date = today + timedelta(days=loan.requested_days)

            # 2. Statusni o'zgartiramiz
            loan.status = Loans.Status.BORROWED

            # 3. 'Kim berdi' maydoniga aynan shu tugmani bosgan adminni yozamiz
            loan.issued_by = request.user

            # 4. Kitob nusxasini bazada 'Ijarada' deb band qilamiz
            copy = loan.copy
            copy.status = BookCopies.Status.ON_LOAN
            copy.save(update_fields=["status"])

            # 5. Ijarani saqlaymiz
            loan.save()

            # Tizimga logni yozamiz
            perform_logging(self, loan, SystemLogs.Action.USER_UPDATED, SystemLogs.TargetType.LOAN,
                            details=f"Admin {request.user.username} kitobni topshirdi. Muddat: {loan.due_date}")

            count += 1

        self.message_user(request,  f"{count} ta kitob muvaffaqiyatli topshirildi va ijara muddati boshlandi.", messages.SUCCESS)

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