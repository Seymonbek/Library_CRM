from django.db import models

class Category(models.Model):
    """
    Kitob kategoriyasi. O'z-o'ziga bog'liq.
    Misol: Adabiyot → O'zbek adabiyoti
    """
    name = models.CharField(max_length=100,unique=True, verbose_name="Kategoriya nomi")
    parent_category_id = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, verbose_name="Tegishli bo'lim")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name

class Publisher(models.Model):
    """
    Nashriyot ma'lumotlari.
    """
    name = models.CharField(max_length=150, unique=True, verbose_name="Nashriyot nomi")
    address = models.CharField(max_length=255, blank=True, verbose_name="Manzil")
    phone_number = models.CharField(max_length=13, blank=True, verbose_name="Telefon")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")


    class Meta:
        verbose_name = "Nashriyot"
        verbose_name_plural = "Nashriyotlar"

    def __str__(self):
        return self.name

class Author(models.Model):
    """
    Kitob muallifi.
    Familiyasi va ismi bo'yicha saralanadi.
    """
    first_name = models.CharField(max_length=30, verbose_name="Ism")
    last_name = models.CharField(max_length=30, verbose_name="Familiya")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Tug'ilgan sanasi")
    bio = models.TextField(null=True, blank=True, verbose_name="Biografiyasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Muallif"
        verbose_name_plural = "Mualliflar"

        # Ro'yxatni avtomatik ravishda familiyasi, keyin ismi bo'yicha saralab beradi
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class BookCopies(models.Model):
    """
    Kitobning har bir fizik nusxasi.
    Har nusxaning o'z inventar raqami va holati bor.
    """
    class Condition(models.TextChoices):
        NEW = 'new', 'Yangi',
        GOOD = 'good', 'Yaxshi',
        WORN = 'worn', 'Eskirgan',
        DAMAGED = 'damaged', 'Shikastlangan',

    class Status(models.TextChoices):
        ON_SHELF = 'on_shelf', 'Javonda'
        ON_LOAN = 'on_loan', 'Ijarada'
        IN_REPAIR = 'in_repair', 'Ta\'mirda'
        LOST = 'lost', 'Yo\'qolgan'
        WRITTEN_OFF = 'written_off', 'Hisobdan chiqarilgan'

    book = models.ForeignKey('books.Books', on_delete=models.CASCADE, verbose_name="Kitob")
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name="Inventar raqami")
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEW, verbose_name="Holati")
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.ON_SHELF, verbose_name="Joylashuv holati")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Kitob nusxasi"
        verbose_name_plural = "Kitob nusxalari"

    def __str__(self):
        return f"{self.book.title} — {self.inventory_number}"


class Books(models.Model):
    """
    Asosiy kitob ma'lumotlari.
    Fizik nusxalar BookCopies da saqlanadi.
    """
    class Language(models.TextChoices):
        UZBEK = 'uz', "O'zbekcha"
        RUSSIAN = 'ru', 'Ruscha'
        ENGLISH = 'en', 'Inglizcha'

    title = models.CharField(max_length=255, verbose_name="Kitob nomi")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books", verbose_name="Muallif")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="books", verbose_name="Kategoriya")
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, related_name="books", verbose_name="Nashriyot")
    isbn = models.CharField(max_length=13, unique=True, blank=True, verbose_name="ISBN")
    language = models.CharField(max_length=20, choices=Language.choices, default=Language.UZBEK, verbose_name="Til")
    page_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Sahifalar soni")
    description = models.TextField(null=True, blank=True, verbose_name="Tavsif")
    cover_image = models.CharField(max_length=500, null=True, blank=True, verbose_name="Muqova rasmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"

    def __str__(self):
        return f"{self.title} — {self.author}"