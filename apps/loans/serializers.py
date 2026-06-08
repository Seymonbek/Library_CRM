from django.utils import timezone
from rest_framework import serializers

from apps.loans.models import Loans, Fines, Waitlists, Notifications, SystemLogs, LibrarySettings
from apps.loans.services import create_loan_request, create_waitlist_entry, return_loan
from apps.users.models import User
from apps.users.serializers import UserShortSerializer
from apps.books.models import Books, BookCopies

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
        return obj.status == Loans.Status.BORROWED and obj.due_date is not None and obj.due_date < timezone.now().date()

class LoanCreateSerializer(serializers.Serializer):
    book_id = serializers.PrimaryKeyRelatedField(queryset=Books.objects.all(), source="book",)
    requested_days = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_requested_days(self, value):
        from apps.loans.services import get_max_loan_days
        max_days = get_max_loan_days()
        if value > max_days:
            raise serializers.ValidationError(f"Maksimal ruxsat etilgan muddat {max_days} kun")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        return create_loan_request(
            user=request.user,
            book=validated_data["book"],
            requested_days=validated_data["requested_days"],
            notes=validated_data.get("notes", "")
        )

class LoanReturnSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        request = self.context["request"]
        loan = self.instance
        notes = self.validated_data.get("notes", loan.notes)
        return return_loan(loan=loan, actor=request.user, notes=notes)

    
class FineSerializer(serializers.ModelSerializer):
    
    loan = LoanListSerializer(read_only=True)
    paid_by = UserShortSerializer(read_only=True)

    class Meta:
        model = Fines
        fields = ["id", "loan", "amount", "reason", "is_paid", "paid_by", "paid_at", "created_at"]
        read_only_fields = fields


class WaitlistSerializer(serializers.ModelSerializer):

    book = BookShortSerializer(read_only=True)
    user = UserShortSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(queryset=Books.objects.all(), source="book", write_only=True)

    class Meta:
        model = Waitlists
        fields = ["id", "book", "book_id", "user", "status", "notified_at", "created_at"]
        read_only_fields = ["id", "user", "status", "notified_at", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        return create_waitlist_entry(user=request.user, book=validated_data["book"],)
