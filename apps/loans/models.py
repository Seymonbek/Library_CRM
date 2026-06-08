from django.db import models
from django.utils import timezone


class Waitlists(models.Model):
    """
    Kitob navbat tizimi.
    Kitob bo'sh bo'lganda foydalanuvchiga xabar yuboriladi.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Navbatda'
        NOTIFIED = 'notified', 'Xabardor'
        FULFILLED = 'fulfilled', 'Bajarildi'
        CANCELLED = 'cancelled', 'Bekor qilindi'



    book = models.ForeignKey('books.Books', on_delete=models.CASCADE, verbose_name="Kitob")
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING, verbose_name="Holati")
    notified_at = models.DateTimeField(null=True, blank=True, verbose_name="Xabardor qilingan payt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Navbat"
        verbose_name_plural = "Navbatlar"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user} — {self.book} ({self.status})"


class Loans(models.Model):
    """
    Kitob ijarasi yozuvi.
    Kim, qaysi nusxani, qachon oldi va qaytardi.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        BORROWED = 'borrowed', 'Ijarada'
        RETURNED = 'returned', 'Qaytarildi'
        OVERDUE = 'overdue', 'Muddati o\'tdi'
        LOST = 'lost', 'Yo\'qolgan'

    copy = models.ForeignKey('books.BookCopies', on_delete=models.CASCADE, verbose_name="Kitob nusxasi")
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='loans', verbose_name="Foydalanuvchi")
    issued_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name="issued_loans", verbose_name="Kim berdi")
    due_date = models.DateField(verbose_name="Qaytarish muddati", null=True, blank=True)
    requested_days = models.PositiveIntegerField(verbose_name="So'ralgan kunlar", default=10)
    returned_date = models.DateField(null=True, blank=True, verbose_name="Qaytarilgan sana")
    returned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, related_name='returned_loans', null=True, blank=True, verbose_name="Qabul qilingan")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Holati")
    notes = models.TextField(null=True, blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Ijara"
        verbose_name_plural = "Ijaralar"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user} — {self.copy} ({self.status})"

    @property
    def is_overdue(self):
        return (
            self.status == self.Status.BORROWED
            and self.due_date is not None
            and self.due_date < timezone.now().date()
        )

class Fines(models.Model):
    """
    Jarima yozuvi.
    Kech qaytarish, kitob shikastlanishi yoki yo'qolishi uchun.
    """
    class Reason(models.TextChoices):
        LATE_RETURN = 'late_return', 'Kech qaytarish'
        BOOK_DAMAGED = 'book_damaged', 'Kitob shikastlangan'
        BOOK_LOST = 'book_lost', 'Kitob yo\'qolgan'

    loan = models.ForeignKey('Loans', on_delete=models.CASCADE, related_name='fines', verbose_name="Ijara")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Summa")
    reason = models.CharField(max_length=25, choices=Reason.choices, verbose_name="Jarima sababi")
    is_paid = models.BooleanField(default=False, verbose_name="To'langan")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="To'langan vaqt")
    paid_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='paid_fines', verbose_name="Kim to'ladi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Jarima"
        verbose_name_plural = "Jarimalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.loan} — {self.amount}"

    @property
    def is_unpaid(self):
        """To'lanmagan jarima bormi?"""
        return not self.is_paid

class Notifications(models.Model):
    """
    Bot orqali foydalanuvchiga yuborilgan xabarlar.
    Celery task shu jadvaldan o'qib xabar yuboradi.
    """
    class Type(models.TextChoices):
        DUE_REMINDER = 'due_reminder', 'Muddat eslatmasi'
        OVERDUE_ALERT = 'overdue_alert', 'Muddati o\'tdi'
        WAITLIST_READY = 'waitlist_ready', 'Kitob bo\'shadi'
        FINE_ISSUED = 'fine_issued', 'Jarima yozildi'

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications', verbose_name="Foydalanuvchi")
    type = models.CharField(max_length=25, choices=Type.choices, verbose_name="Xabar turi")
    message = models.TextField(verbose_name="Xabar matni")
    is_sent = models.BooleanField(default=False, verbose_name="Xabar yuborildimi")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Yuborilgan vaqt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.type}"

class SystemLogs(models.Model):
    # Audit trail.
    class Action(models.TextChoices):
        USER_REGISTERED = "user_registered", "Foydalanuvchi ro'yxatdan o'tdi"
        USER_UPDATED = "user_updated", "Foydalanuvchi yangilandi"
        USER_BLOCKED = "user_blocked", "Foydalanuvchi bloklandi"
        USER_UNBLOCKED = "user_unblocked", "Foydalanuvchi blokdan ochildi"

        BOOK_ADDED = "book_added", "Kitob qo'shildi"
        BOOK_UPDATED = "book_updated", "Kitob yangilandi"
        BOOK_DELETED = "book_deleted", "Kitob o'chirildi"

        AUTHOR_ADDED = "author_added", "Muallif qo'shildi"
        AUTHOR_UPDATED = "author_updated", "Muallif yangilandi"
        AUTHOR_DELETED = "author_deleted", "Muallif o'chirildi"

        PUBLISHER_ADDED = "publisher_added", "Nashriyot qo'shildi"
        PUBLISHER_UPDATED = "publisher_updated", "Nashriyot yangilandi"
        PUBLISHER_DELETED = "publisher_deleted", "Nashriyot o'chirildi"

        CATEGORY_ADDED = "category_added", "Kategoriya qo'shildi"
        CATEGORY_UPDATED = "category_updated", "Kategoriya yangilandi"
        CATEGORY_DELETED = "category_deleted", "Kategoriya o'chirildi"

        BOOK_COPY_ADDED = "book_copy_added", "Kitob nusxasi qo'shildi"
        BOOK_COPY_UPDATED = "book_copy_updated", "Kitob nusxasi yangilandi"
        BOOK_COPY_DELETED = "book_copy_deleted", "Kitob nusxasi o'chirildi"

        LOAN_REQUESTED = "loan_requested", "Ijara so'rovi yaratildi"
        LOAN_APPROVED = "loan_approved", "Ijara so'rovi tasdiqlandi"
        LOAN_RETURNED = "loan_returned", "Kitob qaytarildi"

        FINE_ADDED = "fine_added", "Jarima yozildi"
        FINE_PAID = "fine_paid", "Jarima to'landi"

        WAITLIST_CREATED = "waitlist_created", "Navbat yaratildi"
        WAITLIST_STATUS_CHANGED = "waitlist_status_changed", "Navbat holati o'zgardi"

    class TargetType(models.TextChoices):
        USER = "user", "Foydalanuvchi"
        BOOK = "book", "Kitob"
        AUTHOR = "author", "Muallif"
        PUBLISHER = "publisher", "Nashriyot"
        CATEGORY = "category", "Kategoriya"
        BOOK_COPY = "book_copy", "Kitob nusxasi"
        LOAN = "loan", "Ijara"
        FINE = "fine", "Jarima"
        WAITLIST = "waitlist", "Navbat"
        NOTIFICATION = "notification", "Xabar"

    admin = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='system_logs', verbose_name="Admin")
    action = models.CharField(max_length=50, choices=Action.choices, verbose_name="Amal")
    target = models.IntegerField(null=True, blank=True, verbose_name="Ob'ekt ID")
    target_type = models.CharField(max_length=20,null=True, blank=True, choices=TargetType.choices, verbose_name="Ob'ekt turi")
    details = models.TextField(null=True, blank=True, verbose_name="Tafsilotlar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Loglar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin} — {self.action} — {self.target}"

class LibrarySettings(models.Model):
    """
    Kutubxona uchun global sozlamalar
    """

    daily_fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00, verbose_name="Kunlik jarima miqdori (so'm)")
    max_loan_days = models.PositiveIntegerField(default=10, verbose_name="Maksimal ijara muddati (kun)")

    class Meta:
        verbose_name = "Tizim sozlamasi"
        verbose_name_plural = "Tizim sozlamalari"

    def __str__(self):
        return "Global sozlamalar"

    # Admin panelda ikkinchi yozuv qo'shishni taqiqlash uchun save'ni override qilamiz
    def save(self, *args, **kwargs):
        if not self.pk and LibrarySettings.objects.exists():
            raise ValueError("Faqat bitta sozlama yozuvi bo'lishi mumkin")
        return super().save(*args, **kwargs)