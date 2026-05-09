Library Management CRM System

Ushbu loyiha kutubxona faoliyatini avtomatlashtirish uchun mo'ljallangan
professional boshqaruv tizimidir. Tizim yordamida kitoblar zaxirasini
boshqarish, ijaraga berish jarayonlarini nazorat qilish, jarimalarni hisoblash
va foydalanuvchilar bilan Telegram bot orqali muloqot qilish imkoniyatlari
yaratilgan.

Asosiy funksional imkoniyatlar

Tizim quyidagi muhim biznes jarayonlarini o'z ichiga oladi:

1.  Foydalanuvchilar va rollar: Tizimda Super Admin, Admin va O'quvchi rollari
    mavjud. Har bir rol uchun alohida ruxsatnomalar (Permissions) o'rnatilgan
    bo'lib, ular xavfsizlikni ta'minlaydi.
2.  Kitoblar va nusxalar nazorati: Har bir kitobning umumiy ma'lumotlaridan
    tashqari, uning har bir fizik nusxasi (BookCopies) alohida inventar raqami,
    holati va hozirgi statusi bilan kuzatib boriladi.
3.  Avtomatlashgan ijara tizimi: Kitob ijaraga berilayotgan paytda tizim
    foydalanuvchining bloklanmaganligini va omborda bo'sh nusxa borligini
    avtomatik tekshiradi. Nusxa berilganda uning holati band qilinadi.
4.  Dinamik jarima hisoblash: Kitobni qaytarish vaqtida, agar belgilangan
    muddatdan kechikish bo'lsa, tizim sozlamalarda ko'rsatilgan kunlik tarif
    bo'yicha avtomatik jarima hisoblaydi va foydalanuvchi balansini yangilaydi.
5.  Tizim loglari (Audit Trail): Kutubxonachilar tomonidan bajarilgan har bir
    muhim amal (kitob qo'shish, o'chirish, status o'zgartirish) SystemLogs
    jadvalida saqlanib boriladi. Bu ma'lumotlarni o'chirish yoki o'zgartirish
    imkoniyati cheklangan.
6.  Telegram Bot integratsiyasi: O'quvchilar uchun kitoblarni qidirish, o'z
    ijaralarini ko'rish va tizimdan bildirishnomalar olish uchun Aiogram
    kutubxonasida yozilgan interfeys mavjud.

Texnologik stek

  - Backend: Django 5.x, Django REST Framework
  - Autentifikatsiya: JWT (SimpleJWT)
  - Ma'lumotlar bazasi: PostgreSQL (Production), SQLite (Development)
  - Dokumentatsiya: Swagger va ReDoc (drf-spectacular)
  - Telegram Bot: Aiogram 3.x
  - Admin interfeys: Django Unfold

Loyiha strukturasi

Loyiha modulli arxitektura asosida qurilgan:

  - apps/users: Foydalanuvchilar profili, rollar va ruxsatnomalar boshqaruvi.
  - apps/books: Mualliflar, kategoriyalar, nashriyotlar va kitob nusxalari
    bazasi.
  - apps/loans: Ijara operatsiyalari, jarima hisob-kitoblari va global
    sozlamalar.
  - apps/bot: Telegram bot mantiqi va API bilan bog'lanish qismi.
  - config: Loyihaning umumiy sozlamalari va URL yo'llari.

O'rnatish va ishga tushirish

1.  Loyihani yuklab oling va virtual muhitni yarating:

git clone https://github.com/username/library-crm.git
cd library-crm
python -m venv venv
source venv/bin/activate  # Windows uchun: venv\Scripts\activate
pip install -r requirements.txt

2.  Konfiguratsiyani sozlang: Loyiha ildizida .env faylini yarating va quyidagi
    o'zgaruvchilarni kiriting:

  - SECRET_KEY (Django maxfiy kaliti)
  - DEBUG (True yoki False)
  - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT (Bazaga ulanish
    ma'lumotlari)
  - BOT_TOKEN (Telegram bot tokeni)

3.  Ma'lumotlar bazasini tayyorlang:

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

4.  Serverlarni ishga tushiring:

python manage.py runserver  # API server
python apps/bot/main.py     # Telegram bot (alohida terminalda)

API va Admin panel

Loyiha ishga tushgandan so'ng quyidagi interfeyslar mavjud bo'ladi:

  - Swagger UI: http://localhost:8000/api/swagger/
  - Admin panel: http://localhost:8000/admin/

Muhim eslatma

Tizim to'g'ri ishlashi uchun admin panelga kirib, LibrarySettings (Tizim
sozlamalari) bo'limida birinchi sozlama yozuvini yaratishingiz kerak. Bunda
kunlik jarima miqdori va maksimal ijara muddati kabi parametrlar belgilanadi.
Ushbu ma'lumotlarsiz jarima hisoblash tizimi ishlamasligi mumkin.
