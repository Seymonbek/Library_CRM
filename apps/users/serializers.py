from django.db import transaction
from rest_framework import serializers
from apps.loans.models import SystemLogs
from apps.loans.utils import perform_logging
# get_user_model o'rniga to'g'ridan-to'g'ri import IDE uchun yaxshiroq
from .models import User


class UserShortSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi haqida qisqa ma'lumot (boshqa applar uchun).
    """

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "phone_number", "role"]
        read_only_fields = ["id"]


class UserSerializer(serializers.ModelSerializer):
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
        read_only_fields = ["id", "date_joined", "is_blocked"]

    @transaction.atomic
    def update(self, instance, validated_data):
        # 1. Eski holatlarni saqlab olamiz
        old_status = instance.status
        old_role = instance.role

        # 2. Ma'lumotlarni yangilaymiz
        user = super().update(instance, validated_data)

        # 3. Status o'zgarishi (Bloklash/Ochish) logi
        if user.status != old_status:
            if user.status == User.Status.BLOCKED:
                action = SystemLogs.Action.USER_BLOCKED
                msg = "Bloklandi"
            else:
                action = SystemLogs.Action.USER_UNBLOCKED
                msg = "Blokdan ochildi"

            perform_logging(self, user, action, SystemLogs.TargetType.USER,
                            details=f"Foydalanuvchi statusi o'zgardi: {msg}")

        # 4. Rol o'zgarishi logi
        if user.role != old_role:
            perform_logging(self, user, SystemLogs.Action.USER_UPDATED, SystemLogs.TargetType.USER,
                            details=f"Rol o'zgardi: {old_role} -> {user.role}")

        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Yangi foydalanuvchini ro'yxatdan o'tkazish.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ["phone_number", "first_name", "last_name", "password", "role"]

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan")
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        perform_logging(self, user, SystemLogs.Action.USER_REGISTERED, SystemLogs.TargetType.USER,
                        details=f"Yangi foydalanuvchi: {user.phone_number}")
        return user