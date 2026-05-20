from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.loans.models import SystemLogs
from apps.loans.utils import perform_logging
from .models import User

def normalize_phone_number(value: str) -> str:
    return value.strip().replace(" ", "")

def build_unique_username(phone_number: str) -> str:
    base = "".join(ch for ch in phone_number if ch.isdigit()) or "user"
    username = base

    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}_{counter}"
        counter += 1

    return username


class UserShortSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi haqida qisqa ma'lumot (boshqa applar uchun).
    """

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "phone_number", "role"]
        read_only_fields = ["id"]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi profilini ko'rish va tahrirlash.
    """
    # is_blocked property bo'lgani uchun uni faqat o'qish uchun chiqarish mumkin
    is_blocked = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "phone_number", "first_name", "last_name",
            "role", "status", "is_blocked", "is_active", "date_joined"
        ]
        read_only_fields = fields

 
class UserSelfUpdateSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi o'z profilini yangilashi uchun serializer.
    """
    class Meta:
        model = User
        fields = ["phone_number", "first_name", "last_name"]

    def validate_phone_number(self, value):
        value = normalize_phone_number(value)
        
        qs = User.objects.filter(phone_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan")
        return value


class UserAdminSerializer(serializers.ModelSerializer):
    """
    Adminlar uchun foydalanuvchi ma'lumotlarini ko'rish va tahrirlash.
    """
    class Meta:
        model = User
        fields = [
            "id", "username", "phone_number", "first_name", "last_name", "role",
            "status", "balance", "is_active", "is_blocked", "date_joined"
        ]

        read_only_fields = ["id", "is_blocked", "date_joined"]

    def validate_phone_number(self, value):
        value = normalize_phone_number(value)
        
        qs = User.objects.filter(phone_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan")
        return value
    

    @transaction.atomic
    def update(self, instance, validated_data):
        old_status = instance.status
        old_role = instance.role

        user = super().update(instance, validated_data)

        if user.status != old_status:
            action = (SystemLogs.Action.USER_BLOCKED 
                      if user.status == User.Status.BLOCKED else SystemLogs.Action.USER_UNBLOCKED)
            perform_logging(self, user, action, SystemLogs.TargetType.USER, details=f"Foydalanuvchi statusi o'zgardi: {old_status} -> {user.status}",)

        if user.role != old_role:
            perform_logging(self, user, SystemLogs.Action.USER_UPDATED, SystemLogs.TargetType.USER, details=f"Foydalanuvchi roli o'zgardi: {old_role} -> {user.role}",)

        return user
    

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Yangi foydalanuvchini ro'yxatdan o'tkazish.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ["phone_number", "first_name", "last_name", "password"]

    def validate_phone_number(self, value):
        value = normalize_phone_number(value)
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan")
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        phone_number = validated_data["phone_number"]
        
        user = User(
            username=build_unique_username(phone_number),
            phone_number=phone_number,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Role.USER,
            status=User.Status.ACTIVE,
        )
        user.set_password(password)
        user.save()

        perform_logging(self, user, SystemLogs.Action.USER_REGISTERED, SystemLogs.TargetType.USER,
                        details=f"Yangi foydalanuvchi: {user.phone_number}")
        return user
    

class PhoneTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        username = attrs.get("username", "").strip()
        phone_number = normalize_phone_number(attrs.get("phone_number", ""))
        password = attrs.get("password", "")

        if not username and not phone_number:
            raise serializers.ValidationError(
                {"detail": "username yoki phone_number yuborilishi kerak"}
            )

        user = None

        if phone_number:
            user = User.objects.filter(phone_number=phone_number).first()

        if user is None and username:
            user = User.objects.filter(username=username).first()

        if user is None:
            raise serializers.ValidationError(
                {"detail": "Login yoki parol noto'g'ri"}
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"detail": "Login yoki parol noto'g'ri"}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Bu akkaunt faol emas"}
            )

        if user.status == User.Status.BLOCKED:
            raise serializers.ValidationError(
                {"detail": "Bu akkaunt bloklangan"}
            )

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserShortSerializer(user).data,
        }