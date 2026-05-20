from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.books.models import BookCopies, Books
from apps.users.models import User
from .models import Fines, LibrarySettings, Loans, Notifications, SystemLogs, Waitlists
from .utils import perform_logging


def get_library_settings():
    return LibrarySettings.objects.first()


def get_max_loan_days():
    settings = get_library_settings()
    return settings.max_loan_days if settings else 10


def get_daily_fine_amount():
    settings = get_library_settings()
    return settings.daily_fine_amount if settings else Decimal("2000.00")


@transaction.atomic
def create_loan_request(*, user: User, book: Books, requested_days: int, notes: str = ""):
    if user.status == User.Status.BLOCKED:
        raise ValidationError({"detail": "Bloklangan foydalanuvchi kitob so'ray olmaydi"})

    if requested_days <= 0:
        raise ValidationError({"requested_days": "Kunlar soni 0 dan katta bo'lishi kerak"})

    max_days = get_max_loan_days()
    if requested_days > max_days:
        raise ValidationError(
            {"requested_days": f"Maksimal ruxsat etilgan muddat {max_days} kun"}
        )

    active_statuses = [Loans.Status.PENDING, Loans.Status.BORROWED, Loans.Status.OVERDUE]
    if Loans.objects.filter(
        user=user,
        copy__book=book,
        status__in=active_statuses,
    ).exists():
        raise ValidationError(
            {"book_id": "Sizda bu kitob uchun faol so'rov yoki ijara allaqachon mavjud"}
        )

    available_copy = (
        BookCopies.objects.select_for_update()
        .filter(book=book, status=BookCopies.Status.ON_SHELF)
        .order_by("id")
        .first()
    )

    if not available_copy:
        raise ValidationError({"book_id": "Bu kitobdan bo'sh nusxa qolmagan"})

    loan = Loans.objects.create(
        copy=available_copy,
        user=user,
        requested_days=requested_days,
        notes=notes,
        status=Loans.Status.PENDING,
    )

    perform_logging(
        actor=user,
        instance=loan,
        action_type=SystemLogs.Action.LOAN_REQUESTED,
        target_type=SystemLogs.TargetType.LOAN,
        details=(
            f"Foydalanuvchi {user.phone_number or user.username} "
            f"'{book.title}' kitobi uchun {requested_days} kunlik so'rov yubordi"
        ),
    )
    return loan


@transaction.atomic
def approve_loan_request(*, loan: Loans, actor: User):
    if loan.status != Loans.Status.PENDING:
        raise ValidationError({"detail": "Faqat pending so'rov tasdiqlanishi mumkin"})

    if loan.user.status == User.Status.BLOCKED:
        raise ValidationError({"detail": "Bloklangan foydalanuvchiga kitob berib bo'lmaydi"})

    copy = (
        BookCopies.objects.select_for_update()
        .filter(pk=loan.copy_id)
        .select_related("book")
        .first()
    )

    if copy is None:
        raise ValidationError({"detail": "Kitob nusxasi topilmadi"})

    if copy.status != BookCopies.Status.ON_SHELF:
        replacement_copy = (
            BookCopies.objects.select_for_update()
            .filter(book=copy.book, status=BookCopies.Status.ON_SHELF)
            .exclude(pk=copy.pk)
            .order_by("id")
            .first()
        )

        if replacement_copy is None:
            raise ValidationError({"detail": "Tasdiqlash vaqtida bo'sh nusxa topilmadi"})

        copy = replacement_copy
        loan.copy = copy

    copy.status = BookCopies.Status.ON_LOAN
    copy.save(update_fields=["status"])

    loan.status = Loans.Status.BORROWED
    loan.issued_by = actor
    loan.due_date = timezone.now().date() + timedelta(days=loan.requested_days)
    loan.save(update_fields=["copy", "status", "issued_by", "due_date"])

    perform_logging(
        actor=actor,
        instance=loan,
        action_type=SystemLogs.Action.LOAN_APPROVED,
        target_type=SystemLogs.TargetType.LOAN,
        details=(
            f"Admin {actor.username} loan #{loan.pk} so'rovini tasdiqladi. "
            f"Qaytarish muddati: {loan.due_date}"
        ),
    )
    return loan


@transaction.atomic
def return_loan(*, loan: Loans, actor: User, notes: str | None = None):
    if loan.status not in [Loans.Status.BORROWED, Loans.Status.OVERDUE]:
        raise ValidationError(
            {"detail": "Faqat ijaradagi yoki overdue holatdagi kitob qaytarilishi mumkin"}
        )

    today = timezone.now().date()

    copy = BookCopies.objects.select_for_update().get(pk=loan.copy_id)
    user = User.objects.select_for_update().get(pk=loan.user_id)

    loan.status = Loans.Status.RETURNED
    loan.returned_date = today
    loan.returned_to = actor
    if notes is not None:
        loan.notes = notes
    loan.save(update_fields=["status", "returned_date", "returned_to", "notes"])

    copy.status = BookCopies.Status.ON_SHELF
    copy.save(update_fields=["status"])

    if loan.due_date and today > loan.due_date:
        delay_days = (today - loan.due_date).days
        fine_amount = Decimal(delay_days) * get_daily_fine_amount()

        fine = Fines.objects.create(
            loan=loan,
            amount=fine_amount,
            reason=Fines.Reason.LATE_RETURN,
        )

        user.balance -= fine_amount
        user.save(update_fields=["balance"])

        Notifications.objects.create(
            user=user,
            type=Notifications.Type.FINE_ISSUED,
            message=(
                f"Sizga {delay_days} kun kechikkaningiz uchun "
                f"{fine_amount} so'm jarima yozildi."
            ),
        )

        perform_logging(
            actor=actor,
            instance=fine,
            action_type=SystemLogs.Action.FINE_ADDED,
            target_type=SystemLogs.TargetType.FINE,
            details=(
                f"Loan #{loan.pk} kech qaytarildi. "
                f"{delay_days} kun kechikish uchun {fine_amount} so'm jarima yozildi."
            ),
        )

    next_waitlist = (
        Waitlists.objects.select_for_update()
        .filter(book=copy.book, status=Waitlists.Status.PENDING)
        .order_by("created_at")
        .first()
    )

    if next_waitlist:
        next_waitlist.status = Waitlists.Status.NOTIFIED
        next_waitlist.notified_at = timezone.now()
        next_waitlist.save(update_fields=["status", "notified_at"])

        Notifications.objects.create(
            user=next_waitlist.user,
            type=Notifications.Type.WAITLIST_READY,
            message=f"'{copy.book.title}' kitobi bo'shadi. Endi so'rov yuborishingiz mumkin.",
        )

        perform_logging(
            actor=actor,
            instance=next_waitlist,
            action_type=SystemLogs.Action.WAITLIST_STATUS_CHANGED,
            target_type=SystemLogs.TargetType.WAITLIST,
            details=f"Waitlist #{next_waitlist.pk} holati NOTIFIED ga o'tdi",
        )

    perform_logging(
        actor=actor,
        instance=loan,
        action_type=SystemLogs.Action.LOAN_RETURNED,
        target_type=SystemLogs.TargetType.LOAN,
        details=f"Loan #{loan.pk} bo'yicha kitob qaytarildi",
    )
    return loan


@transaction.atomic
def pay_fine(*, fine: Fines, actor: User):
    if fine.is_paid:
        raise ValidationError({"detail": "Bu jarima allaqachon to'langan"})

    fine.is_paid = True
    fine.paid_at = timezone.now()
    fine.paid_by = actor
    fine.save(update_fields=["is_paid", "paid_at", "paid_by"])

    user = User.objects.select_for_update().get(pk=fine.loan.user_id)
    user.balance += fine.amount
    user.save(update_fields=["balance"])

    perform_logging(
        actor=actor,
        instance=fine,
        action_type=SystemLogs.Action.FINE_PAID,
        target_type=SystemLogs.TargetType.FINE,
        details=(
            f"Loan #{fine.loan_id} bo'yicha {fine.amount} so'm jarima to'landi. "
            f"Qabul qiluvchi: {actor.username}"
        ),
    )
    return fine


@transaction.atomic
def create_waitlist_entry(*, user: User, book: Books):
    if user.status == User.Status.BLOCKED:
        raise ValidationError({"detail": "Bloklangan foydalanuvchi navbatga tura olmaydi"})

    if BookCopies.objects.filter(book=book, status=BookCopies.Status.ON_SHELF).exists():
        raise ValidationError({"book_id": "Bu kitob hozir mavjud, navbatga turish shart emas"})

    if Waitlists.objects.filter(
        user=user,
        book=book,
        status__in=[Waitlists.Status.PENDING, Waitlists.Status.NOTIFIED],
    ).exists():
        raise ValidationError({"book_id": "Siz bu kitob uchun allaqachon navbatdasiz"})

    waitlist = Waitlists.objects.create(
        user=user,
        book=book,
        status=Waitlists.Status.PENDING,
    )

    perform_logging(
        actor=user,
        instance=waitlist,
        action_type=SystemLogs.Action.WAITLIST_CREATED,
        target_type=SystemLogs.TargetType.WAITLIST,
        details=f"{user.phone_number or user.username} foydalanuvchi '{book.title}' kitobi uchun navbatga qo'shildi",
    )
    return waitlist