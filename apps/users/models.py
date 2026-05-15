from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Foydalanuvchi modeli.
    3 ta rol: super_admin, admin, reader.
    Telegram bot va Django admin orqali kirish mumkin.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'Foydalanuvchi'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        BLOCKED = 'blocked', 'Bloklangan'

    # Telegram ID 2.1 milliarddan oshib ketgani uchun qilingan va DataError bermasligi uchun BigInt ishlatildi (Tg IDlar juda uzun)
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)
    phone_number = models.CharField(max_length=13, blank=True, verbose_name="Telefon")
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.USER, verbose_name="Rol")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Balans")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE, verbose_name="Holat")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")


    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    # Admin panelda Ali Valiyev (admin) ko'rinishida chiqadi
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    # Mantiqiy tekshiruvlar
    @property # Propertyni o'zgartirib bo'lmaydi uni faqat o'qish uchun chaqirish mumkin
    def can_manage_books(self):
        """Faqat admin va super admin kitoblar bilan ishlay oladi"""
        return self.role in [self.Role.ADMIN, self.Role.SUPER_ADMIN]

    @property
    def is_blocked(self):
        """Foydalanuvchi blocklanganmi"""
        return self.status == self.Status.BLOCKED

    @property
    def has_debt(self):
        """Foydalanuvchining qarzi bormi"""
        return self.balance < 0