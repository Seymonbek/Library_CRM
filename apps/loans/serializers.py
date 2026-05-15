from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.loans.models import Loans, Fines, Waitlists, Notifications, SystemLogs, LibrarySettings
from apps.users.models import User
from apps.books.models import Books, BookCopies
from .utils import perform_logging

class UserShortSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi haqida qisqacha ma'lumot beruvchi serializer.

    Ushbu serializer foydalanuvchining faqat asosiy maydonlarini (ism, familiya,
    telefon raqami va roli) qaytaradi. Bu ma'lumotlar odatda ijara (loan) yoki
    navbat (waitlist) kabi boshqa serializerlar ichida "nested" (ichma-ich)
    holatda foydalanish uchun mo'ljallangan
    """
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "phone_number", "role"]
        read_only_fields = ["id"]

class BookShortSerializer(serializers.ModelSerializer):
    """
    Kitob haqida asosiy ma'lumotlarni ko'rsatuvchi serializer.

    Bu serializer kitobning nomi va ISBN raqamidan tashqari,
    muallifning ism-sharifini `author_name` maydoni orqali
    birlashtirilgan holda taqdim etadi
    """
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Books
        fields = ["id", "title", "author_name", "isbn", "language"]

    def get_author_name(self, obj) -> str:
        """Muallifning ismi va familiyasini birlashtirib qaytaradi."""
        return f"{obj.author.first_name} {obj.author.last_name}"

class BookCopyShortSerializer(serializers.ModelSerializer):
    """
    Kitob nusxasi haqida ma'lumot beruvchi serializer.

    Ushbu serializer kitobning o'zi haqidagi qisqa ma'lumotni (BookShortSerializer orqali)
    va har bir nusxaga tegishli bo'lgan inventar raqami, holati hamda hozirgi
    statusini (masalan: kutubxonada, ijarada, yo'qolgan) o'z ichiga oladi.
    """
    book = BookShortSerializer(read_only=True)

    class Meta:
        model = BookCopies
        fields = ['id', 'book', 'inventory_number', 'condition', 'status']

class LoanListSerializer(serializers.ModelSerializer):
    """
    Ijara yozuvlarini ro'yxat ko'rinishida ko'rsatish uchun serializer.

    Ushbu serializer ijara haqidagi barcha asosiy ma'lumotlarni o'z ichiga oladi:
    Foydalanuvchi (UserShortSerializer orqali)
    Kitob nusxasi (BookCopySerializer orqali)
    Ijara sanalari va holati (status)

    Bu ko'rinish kutubxonachiga kim qaysi kitobni qachon qaytarishi kerakligini
    tezda ko'rish imkonini beradi.
    """
    copy = BookCopyShortSerializer(read_only=True)
    user = UserShortSerializer(read_only=True)
    issued_by = UserShortSerializer(read_only=True)
    returned_to = UserShortSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Loans
        fields = ["id", "copy", "user", "issued_by", "due_date", "returned_date",
                  "returned_to", "status", "notes", "is_overdue", "created_at"
                  ]

    def get_is_overdue(self, obj) -> bool:
        """
        Ijaraga olingan kitobning qaytarish muddati o'tganligini aniqlaydi.

        Agar kitob hali qaytarilmagan bo'lsa (BORROWED) va
        bugungi sana qaytarish muddatidan (due_date) katta bo'lsa,
        True qiymatini qaytaradi. Aks holda False.
        """
        return obj.status == Loans.Status.BORROWED and obj.due_date < timezone.now().date()

class LoanCreateSerializer(serializers.ModelSerializer):
    """
    Yangi ijara yozuvini yaratish uchun serializer.

    Ushbu serializer foydalanuvchidan faqat kerakli ID larni qabul qiladi:
    Kitob nusxasining ID raqami.
    Kitob oluvchi foydalanuvchi ID raqami.
    Qaytarish muddati.

    `ListSerializer`dan farqli o'laroq, bu yerda nested (ichma-ich)
    serializerlar ishlatilmaydi, chunki yangi ma'lumot yaratishda
    faqat ob'ektlarning ID raqamlarini yuborish yetarli hisoblanadi.
    """
    book_id = serializers.PrimaryKeyRelatedField(queryset=Books.objects.all(), source="book", write_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)

    class Meta:
        model = Loans
        fields = ["id", "book_id", "user_id", "requested_days", "notes"]
        read_only_fields = ["id"]

    def validate_user(self, value):
        """Foydalanuvchi bloklanmaganligini tekshirish."""
        if value.is_blocked:
            raise serializers.ValidationError("Bu foydalanuvchi bloklangan")

        if value.status == User.Status.BLOCKED:
            raise serializers.ValidationError("Bloklangan foydalanuvchiga kitob berish mumkin emas!")

        return value

    def validate(self, data):
        """Umumiy mantiqiy tekshiruv: Kitob nusxasi bo'shmi?"""
        book = data["book"]
        available_copy = BookCopies.objects.filter(book=book, status=BookCopies.Status.ON_SHELF).select_for_update().first()

        if not available_copy:
            raise serializers.ValidationError({"book_id": "Kechirasiz, bu kitobdan bo‘sh nusxa qolmagan."})
        data["copy"] = available_copy
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Ijara yaratilganda kitob holatini 'borrowed'ga o'zgartirish."""
        validated_data.pop("book")
        copy = validated_data.pop("copy")
        request = self.context.get("request")

        # Ijara yaratish
        loan = Loans.objects.create(copy=copy, status=Loans.Status.PENDING, **validated_data)

        perform_logging(self, loan, SystemLogs.Action.LOAN_CREATED, SystemLogs.TargetType.LOAN,
                        details=f"Kitobga bron (so'rov) yuborildi: {copy.inventory_number}")

        return loan
#
class LoanReturnSerializer(serializers.ModelSerializer):
    """
    Kitobni qaytarib topshirish jarayoni uchun serializer.
    """
    class Meta:
        model = Loans
        fields = ["notes"]

    def validate(self,data):
        loan = self.instance

        if loan.status == Loans.Status.RETURNED:
            raise serializers.ValidationError("Bu kitob allaqachon qaytarilgan.")
        allowed_statuses = [Loans.Status.BORROWED, Loans.Status.OVERDUE]

        if loan.status not in allowed_statuses:
            raise serializers.ValidationError({
                "status": f"Kitobni qaytarish uchun u ijarada bo'lishi kerak. Hozirgi holat: {loan.get_status_display()}"
            })
        return data

    @transaction.atomic
    def save(self, **kwargs):
        loan = self.instance
        request = self.context.get("request")
        today = timezone.now().date()

        # Bazdan kunlik jarima miqdorini olamiz
        settings = LibrarySettings.objects.first()

        # Agar admin sozlamasa default 2000
        daily_rate = settings.daily_fine_amount if settings else Decimal('2000.00')

        # 1. Ijara yopish
        loan.status = Loans.Status.RETURNED
        loan.returned_date = today
        loan.returned_to = request.user if request else None
        loan.notes = self.validated_data.get("notes", loan.notes)
        loan.save(update_fields=["status", "returned_date", "returned_to", "notes"])

        # 2. Kitobni bo'shatish
        copy = loan.copy
        copy.status = BookCopies.Status.ON_SHELF
        copy.save(update_fields=["status"])

        # Jarima mantiqi
        if today > loan.due_date:
            delay_days = (today - loan.due_date).days
            fine_amount = delay_days * daily_rate

            fine = Fines.objects.create(loan=loan, amount=Decimal(fine_amount), reason=Fines.Reason.LATE_RETURN)

            # Foydalanuvchi balansini yangilash
            user = loan.user
            user.balance -= Decimal(fine_amount)
            user.save(update_fields=["balance"])

            perform_logging(self, fine, SystemLogs.Action.FINE_ADDED, SystemLogs.TargetType.FINE,
                            details=f"Kechikish: {delay_days} kun. Jarima {fine_amount} so'm. Foydalanuvchi: {user.phone_number}")

        # 3. Log yozish
        perform_logging(self, loan, SystemLogs.Action.LOAN_RETURNED, SystemLogs.TargetType.LOAN)
        return loan

class FineSerializer(serializers.ModelSerializer):
    """
    Jarimalar bilan ishlash uchun serializer.

    Ushbu serializer quyidagi imkoniyatlarni beradi:
    1. Jarima haqida to'liq ma'lumot olish bog'langan ijara va to'lovchi ma'lumotlari bilan.
    2. Yangi jarima yozish ijara ID si orqali.
    3. To'lov holatini kuzatish.
    """
    # Ijara haqida to'liq ma'lumot
    loan = LoanListSerializer(read_only=True)

    # Jarima yozilayotgan ijaraning ID raqami
    loan_id = serializers.PrimaryKeyRelatedField(queryset=Loans.objects.all(), source="loan", write_only=True)

    # Jarimani qabul qilib olgan admin
    paid_by = UserShortSerializer(read_only=True)
    paid_by_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="paid_by", write_only=True, required=False, allow_null=True)

    class Meta:
        model = Fines
        fields = ["id", "loan", "loan_id", "amount", "reason", "is_paid", "paid_at", "paid_by", "paid_by_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    @transaction.atomic
    def create(self, validate_data):
        fine = super().create(validate_data)
        perform_logging(self, fine, SystemLogs.Action.FINE_ADDED, SystemLogs.TargetType.FINE)
        return fine

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        old_is_paid = instance.is_paid # Eski holatni saqlab qolamiz

        fine = super().update(instance, validated_data)

        if fine.is_paid and not old_is_paid: # Yangi holat
            fine.paid_at = timezone.now() # To'langan vaqtni belgilash
            fine.paid_by = request.user if request else None # Kim to'laganini belgilash
            fine.save(update_fields=["paid_at", "paid_by"]) # O'zgarishlarni saqlash

            perform_logging(
                self, fine, SystemLogs.Action.FINE_ADDED, SystemLogs.TargetType.FINE,
                # FINE_PAID action bo'lsa yaxshiroq
                details=f"Jarima {fine.amount} so'm to'landi. To'lovchi: {fine.loan.user.phone_number}."
            )
            return fine

class WaitlistSerializer(serializers.ModelSerializer):
    """
    Kitoblar uchun navbat tizimi serializeri.

    Ushbu serializer foydalanuvchilarga quyidagilar bo'yicha yordam beradi:
    Qaysi foydalanuvchi qaysi kitob uchun navbatda turganini ko'rish.
    Yangi navbat yaratish (kitob ID va foydalanuvchi ID orqali).
    Navbat holatini (kutmoqda, xabardor qilindi, bajarildi) kuzatish.
    """
    # Kitobning nomi va muallifi haqida to'liq ma'lumot.
    book = BookShortSerializer(read_only=True)

    # Navbatda turgan odamning ismi va telefoni.
    user = UserShortSerializer(read_only=True)

    # Navbatga olinayotgan kitobning ID raqami.
    book_id = serializers.PrimaryKeyRelatedField(queryset=Books.objects.all(), source="book", write_only=True)

    # Navbatga qo'yilayotgan foydalanuvchi ID raqami.
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)

    class Meta:
        model = Waitlists
        fields = ["id", "book", "book_id", "user", "user_id", "status", "notified_at", "created_at"]
        read_only_fields = ["id", "notified_at", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        waitlist = super().create(validated_data)
        perform_logging(self, waitlist, SystemLogs.Action.LOAN_CREATED, SystemLogs.TargetType.LOAN,
                       details=f"Navbat yaratildi: {waitlist.user} - {waitlist.book.title}")
        return waitlist

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        old_status = instance.status

        waitlist = super().update(instance, validated_data)

        if waitlist.status != old_status:
            perform_logging(
                self, waitlist, SystemLogs.Action.LOAN_CREATED, SystemLogs.TargetType.LOAN,
                details=f"Navbat {waitlist.user.phone_number} uchun {old_status}dan {waitlist.status}ga o'zgardi."
            )
        return waitlist

class NotificationSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchilar uchun bildirishnomalar yaratish va ko'rish uchun serializer.

    Ushbu serializer tizimda bildirishnomalarni boshqarishga yordam beradi:
    1. Ma'lumot olishda: Foydalanuvchi haqida to'liq ma'lumotni (UserShortSerializer orqali) taqdim etadi.
    2. Ma'lumot yaratishda: Foydalanuvchining faqat ID raqami (`user_id`) orqali xabar biriktirishga imkon beradi.
    3. Bildirishnomaning turi, matni va yuborilganlik holatini kuzatish imkonini beradi.
    """
    user = UserShortSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="user", write_only=True)

    class Meta:
        model = Notifications
        fields = ["id", "user", "user_id", "type", "message", "is_sent", "sent_at", "created_at"]
        read_only_fields = ["id", "sent_at", "created_at"]

class SystemLogSerializer(serializers.ModelSerializer):
    """
    Tizimdagi barcha muhim amallarni jurnalga yozish (logging) uchun serializer.

    Ushbu serializer quyidagi vazifalarni bajaradi:
    1. Kim (admin): Amalni bajargan shaxs haqida ma'lumot beradi.
       Agar amal tizim tomonidan bajarilgan bo'lsa, `null` bo'lishi mumkin.
    2. Nima (action/target): Qaysi obyekt ustida qanday amal bajarilganini tavsiflaydi.
    3. Tafsilotlar (details): O'zgarishlarning batafsil mazmunini saqlaydi.

    Bu ma'lumotlar faqat o'qish (audit) va tizim monitoringi uchun xizmat qiladi.
    """
    admin = UserShortSerializer(read_only=True)
    admin_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="admin", write_only=True, required=False, allow_null=True)

    class Meta:
        model = SystemLogs
        fields = ["id", "admin", "admin_id", "action", "target", "target_type", "details", "created_at"]
        read_only_fields = ["id", "created_at"]

