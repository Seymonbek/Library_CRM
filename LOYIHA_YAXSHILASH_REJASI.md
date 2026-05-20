# Books CRM Loyiha Yaxshilash Rejasi

## Maqsad

Bu hujjatning vazifasi `Books_CRM` loyihasini oddiy o'quv MVP darajasidan ishonchli, testlangan va production'ga yaqin tizim darajasiga olib chiqish uchun aniq yo'l xaritasini berishdir.

Bu yerda 5 ta savolga javob bor:

1. Hozir loyihaning holati qanday.
2. Avval nimani qilish kerak.
3. Qaysi faylga nima yozish yoki o'zgartirish kerak.
4. Nega aynan shu o'zgarish kerak.
5. Qachon ish "tayyor" deb hisoblanadi.

## Hozirgi holat

Loyiha g'oyasi yaxshi:

- modullar mantiqan bo'lingan: `users`, `books`, `loans`, `bot`
- Django + DRF + JWT + Telegram bot + admin panel kombinatsiyasi to'g'ri tanlangan
- kutubxona domeni uchun kerakli asosiy modellar yozilgan

Lekin hozirgi ko'rinishida loyiha hali production darajasida emas. Eng katta muammolar:

- permission va rollar noto'g'ri ishlayapti
- loan va fine jarayonlarida biznes mantiq xatolari bor
- ayrim oqimlar runtime vaqtida yiqilishi mumkin
- testlar yo'q
- bot va API bir-biridan toza ajratilmagan
- README, settings va dependency ro'yxati bir-biriga to'liq mos emas

Shuning uchun ishni chiroyli ko'rinishdan emas, barqarorlik va xavfsizlikdan boshlash kerak.

## Asosiy tamoyil

Bu loyihani zo'r qilish uchun quyidagi ketma-ketlikni buzmaslik kerak:

1. Avval xavfsizlik va access control.
2. Keyin core biznes mantiq.
3. Keyin bot va API integratsiyasi.
4. Keyin testlar.
5. Eng oxirida deploy, monitoring va qo'shimcha qulayliklar.

Agar bu tartib buzilsa, ustiga yozilgan har bir yangi feature keyin yana qayta buziladi.

## Tavsiya etilgan yakuniy daraja

Loyiha oxirida quyidagi holatga kelishi kerak:

- oddiy user boshqa userlarni ko'ra olmaydi va o'zgartira olmaydi
- faqat admin yoki librarian kitob, loan va fine oqimlarini boshqaradi
- bir dona book copy bir vaqtda faqat bitta faol loan bilan bog'lanadi
- fine hisobi noto'g'ri ikki marta yurmaydi
- bot ORM orqali emas, API yoki service orqali ishlaydi
- eng muhim flowlar test bilan yopiladi
- local va production konfiguratsiyasi aniq ajratiladi
- README loyihani noldan ishga tushirish uchun yetarli bo'ladi

---

## 1-Bosqich: Stabilizatsiya va Asosni Tozalash

Bu bosqichni birinchi qilishing shart. Sababi: hozir ayrim joylarda kod ishlayotgandek ko'rinsa ham, tayanch qatlamlar bir-biriga mos emas.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Dependency ro'yxatini to'g'rilash | `requirements.txt` | Real ishlatilayotgan paketlarni ro'yxatga kirit. Ayniqsa `django-unfold`ni qo'sh. Keraksiz yoki ishlatilmayotgan paketlar bo'lsa qayta ko'rib chiq. | Boshqa muhitda loyiha sinib qolmasligi uchun. | `pip install -r requirements.txt` xatosiz ishlaydi. |
| Django versiyasini bir xillash | `requirements.txt`, virtual environment | Bir xil versiyada ishlashga qaror qil. Kod qaysi Django versiyada sinovdan o'tsa, o'shani pin qil. | Hozir lock qilingan versiya bilan muhitdagi versiya bir xil bo'lmasa, yashirin buglar chiqadi. | Local muhit va requirements bir xil versiyani ko'rsatadi. |
| README ni real kodga moslashtirish | `README.md` | Swagger URL, botni ishga tushirish path'i, DB sozlash tartibi, kerakli env larni yangila. | Hujjat noto'g'ri bo'lsa, loyiha ishonchli ko'rinmaydi. | Noldan kirgan odam README bo'yicha loyihani ochib ishlata oladi. |
| Konfiguratsiyani environment-driven qilish | `config/settings.py`, `.env.example` | SQLite va PostgreSQL tanlovini env orqali boshqar. `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` xavfsiz ishlasin. Production security flaglar uchun joy tayyorla. | Deploy bosqichiga yetganda settings qayta yozilmasligi uchun. | Local va production uchun aniq sozlash modeli paydo bo'ladi. |

### Bu bosqichda aynan nimalarni yozish kerak

`config/settings.py` ichida:

- database tanlash logikasini `DEBUG` yoki alohida `DB_ENGINE` orqali boshqar
- production uchun keyinchalik yoqiladigan `SECURE_*`, cookie va proxy settinglar uchun blok och
- `CORS_ALLOW_ALL_ORIGINS = DEBUG` kabi qisqa yechim o'rniga aniq whitelist ishlatishga tayyorgarlik yarat

`.env.example` ichida:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `BOT_TOKEN`
- `API_BASE_URL`

`README.md` ichida:

- loyiha nima qiladi
- local setup
- migrate
- superuser yaratish
- botni ishga tushirish
- API endpointlar
- default flow: user registration -> book request -> admin approval -> return -> fine

---

## 2-Bosqich: Access Control va Xavfsizlikni To'g'rilash

Bu eng muhim bosqich. Agar shuni to'g'ri qilmasang, qolgan barcha feature'lar xavfli bo'ladi.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Rollar nomini bir xillash | `apps/users/models.py`, `apps/users/permissions.py` | `super_admin` va `admin` nomlari hamma joyda bir xil ishlasin. `superadmin` kabi noto'g'ri string'larni olib tashla. | Hozir permission tekshiruvi noto'g'ri ishlayapti. | Admin va super admin tekshiruvlari real ishlaydi. |
| Custom permissionlar yozish | `apps/users/permissions.py` | Kamida 4 ta permission qatlami yoz: `IsAdminOrSuperAdmin`, `IsLibrarian`, `IsSelfOrAdmin`, `ReadOnlyOrLibrarian`. | Access policy aniq va qayta foydalaniladigan bo'ladi. | Permission logikasi view'lardan ajraladi. |
| User CRUD ni cheklash | `apps/users/views.py`, `apps/users/serializers.py` | Oddiy user faqat o'zini ko'rsin. User list va boshqa user update faqat admin uchun bo'lsin. | Hozir istalgan login qilgan user boshqa userlarni ko'ra olishi mumkin. | `/users/` endpoint xavfsiz ishlaydi. |
| Registratsiyada role writable bo'lmasin | `apps/users/serializers.py` | `role`ni tashqi request'dan qabul qilma yoki faqat admin create flow'da ruxsat ber. Public registration'da default `user` bo'lsin. | Public API orqali admin ochib olish mumkin bo'lmasligi kerak. | Tashqi foydalanuvchi o'zini admin qilib yarata olmaydi. |
| Book va loan endpoint'larini role asosida himoyalash | `apps/books/views.py`, `apps/loans/views.py` | `list/retrieve` uchun bir siyosat, `create/update/delete` uchun boshqa siyosat yoz. | Hamma autentifikatsiyalangan user kitob/fine/loan boshqarmasligi kerak. | Endpointlar rol bo'yicha to'g'ri yopiladi. |

### Aynan qayerga nima yozish kerak

`apps/users/permissions.py` ichida:

- ro'yxatli tekshiruvlar emas, modeldagi role qiymatlariga tayangan aniq permissionlar yoz
- object-level permission ham qo'sh
- faqat `has_permission` emas, kerak bo'lsa `has_object_permission` ham ishlat

`apps/users/views.py` ichida:

- `get_queryset()` yozib, user roliga qarab filter qil
- `get_permissions()`da har bir action uchun aniq policy belgilab chiq
- `create` uchun public registration va admin-created user flow'larini aralashtirma

`apps/books/views.py` ichida:

- `list` va `retrieve` hamma login qilganlar uchun ochiq bo'lishi mumkin
- `create`, `update`, `partial_update`, `destroy` faqat librarian yoki admin uchun bo'lsin

`apps/loans/views.py` ichida:

- oddiy user faqat o'z loanlarini ko'rsin
- fine list ham rolga qarab filtirlansin
- `get_permissions()` ichida permission klass emas, permission instance qaytar

### Nega shunaqa qilish kerak

Sistemada eng xavfli bug bu syntax xato emas, noto'g'ri access control. Chunki unda tizim "ishlaydi", lekin noto'g'ri odam noto'g'ri narsaga kira oladi.

---

## 3-Bosqich: Auth Modelini Bir Qarorga Keltirish

Hozir auth modeli yarim `username`, yarim `phone_number`, yarim Telegram'ga bog'langan. Buni bitta qarorga keltirish kerak.

## Tavsiya

Web/API login uchun `phone_number + password` modelini tanla. `username`ni ichki texnik maydon sifatida qoldirishing mumkin, lekin foydalanuvchiga ko'rsatiladigan login identifikatori telefon bo'lsin.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Login strategiyasini tanlash | `apps/users/models.py`, `apps/users/serializers.py`, `apps/users/views.py` | Custom login serializer yozib, `phone_number` orqali token olish oqimini bir xillash. | Web va bot registratsiyasi bir-biriga mos keladi. | User telefon raqami bilan login qila oladi. |
| Username siyosatini aniq qilish | `apps/users/models.py`, `apps/users/admin.py` | `username` mandatory bo'lsa, qanday to'ldirilishi yozilsin; bo'lmasa custom user model tozalanadi. | Keyin duplicate va auth buglar chiqmasligi uchun. | User yaratish oqimi bitta standart bilan ishlaydi. |
| Telefon raqam validatsiyasini normallashtirish | `apps/users/serializers.py`, bot registration flow | Raqamlarni bitta formatda saqlash qoidasi kirit. | Duplicate userlar va login xatolari kamayadi. | Bir xil telefon bir xil formatda saqlanadi. |

### Qayerga nima yozish kerak

`apps/users/serializers.py` ichida:

- custom login serializer
- registration serializer ichida phone normalization
- public registration va admin registration uchun kerak bo'lsa alohida serializer

`apps/users/views.py` ichida:

- default `TokenObtainPairView` o'rniga custom serializer bilan ishlaydigan login view

`bot/handlers/start.py` ichida:

- botdan ro'yxatdan o'tgan user keyinchalik web/API login bilan zid bo'lmaydigan model ishlat

---

## 4-Bosqich: Loan Domain'ni To'g'ri Arxitekturaga O'tkazish

Bu loyiha yuragi aynan shu joy. Eng ko'p e'tibor shu yerga ketishi kerak.

### Eng to'g'ri yo'l

Loan mantiqini serializer ichidan olib chiqib, service qatlamga ko'chir.

### Tavsiya etilgan yangi fayl

`apps/loans/services.py`

Bu fayl ichida alohida business action'lar bo'lishi kerak:

- `create_loan_request`
- `approve_loan_request`
- `return_loan`
- `pay_fine`
- `create_waitlist_entry`

### Nega aynan service qatlam kerak

Hozir bir xil biznes mantiq serializer, admin action va bot oqimlariga bo'linib ketgan. Bu juda xavfli. Ertaga bitta joyni tuzatsang, ikkinchi joy eski logika bilan qoladi.

Service qatlam bo'lsa:

- API bir xil logikani chaqiradi
- admin bir xil logikani chaqiradi
- bot ham bir xil logikani chaqiradi
- test yozish osonlashadi

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Loan request yaratish logikasini servisga ko'chirish | `apps/loans/services.py`, `apps/loans/serializers.py` | Bo'sh copy topish, blocked user tekshiruvi, duplicate pending request tekshiruvi servisda bo'lsin. | Serializer faqat input/output bilan shug'ullansin. | Loan request bitta joydan boshqariladi. |
| Approval oqimini to'g'rilash | `apps/loans/services.py`, `apps/loans/admin.py`, `apps/loans/views.py` | Pending loan'ni approve qilishda copy hali bo'sh ekanini qayta tekshir. `due_date` va status shu yerda o'zgarsin. | Race condition va noto'g'ri approval'ni oldini oladi. | Bitta copy ikki marta berilmaydi. |
| Return oqimini to'g'rilash | `apps/loans/services.py`, `apps/loans/serializers.py` | Return vaqtida status, returned_date, copy status, fine hisobi, log yozish bitta transaction ichida yurishi kerak. | Kitob qaytishi eng muhim flowlardan biri. | Return flow test bilan yopiladi. |
| Fine to'lovi logikasini to'g'rilash | `apps/loans/services.py`, `apps/loans/views.py`, `apps/loans/serializers.py` | User balance to'lov vaqtida qanday o'zgarishi aniq belgilansin. Bir marta qo'shiladimi yoki ayiriladimi, qaror qat'iy yozilsin. | Hozir balans ikki marta buzilishi mumkin. | Jarima moliyaviy jihatdan to'g'ri ishlaydi. |
| Waitlist biznes qoidalarini aniq qilish | `apps/loans/services.py`, `apps/loans/models.py`, `apps/loans/views.py` | Bir user bir book uchun takror navbatga tusha oladimi yoki yo'q, shuni qat'iy qoidaga aylantir. | Navbat tizimi keyin chalkashib ketmasligi uchun. | Waitlist oqimi aniq bo'ladi. |

### Aynan qayerga nima yozish kerak

`apps/loans/services.py` ichida:

- har bir action uchun bitta public function
- transaction
- validation
- status transition
- log yozish
- kerak bo'lsa notification yaratish

`apps/loans/serializers.py` ichida:

- faqat input validation va response format qoldir
- biznes qarorlarni service'ga delegatsiya qil
- `validate_user` kabi ishlamayotgan hook'larni to'g'ri field name yoki `validate()` ichiga ko'chir

`apps/loans/admin.py` ichida:

- admin action ichida butun logikani yozma
- service function chaqir
- faqat admin UI feedback qaytar

`apps/loans/utils.py` ichida:

- umumiy logging helper'ni serializer context'ga qattiq bog'lab qo'yma
- helper `request`, `actor`, `details`, `target` kabi aniq argument qabul qilsin

`apps/loans/models.py` ichida:

- kerak bo'lsa model-level constraint yoki `clean()` qoidalar qo'sh
- status transition qoidalarini hech bo'lmasa izoh bilan belgilab qo'y

---

## 5-Bosqich: Logging, Audit va Notification'ni Tozalash

Audit trail bu CRM loyihada juda muhim. Lekin logging yordamchi bo'lishi kerak, asosiy flow'ni sindiradigan nuqta emas.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Logging helper'ni universallashtirish | `apps/loans/utils.py`, `apps/books/utils.py` | Bitta umumiy style tanla. `serializer.context`ga bog'liq bo'lmagan, admin action va service'dan ham ishlaydigan helper yoz. | Hozir logging sababli asosiy flow yiqilishi mumkin. | Log helper har joyda bir xil ishlaydi. |
| Action nomlarini to'g'rilash | `apps/loans/models.py` | `LOAN_CREATED`, `LOAN_RETURNED`, `FINE_PAID`, `WAITLIST_CREATED` kabi nomlar real oqimga mos bo'lsin. | Audit ma'lumotlari keyinchalik analytics va troubleshooting uchun kerak bo'ladi. | Action qiymatlari mantiqan to'g'ri bo'ladi. |
| Notification flow'ni aniq qilish | `apps/loans/models.py`, `apps/loans/services.py`, keyin task qatlami | Notification qachon yaratiladi, qachon jo'natiladi, qachon `is_sent=True` bo'ladi, shu model aniq yozilsin. | Bot eslatmalari keyinchalik aynan shu modelga tayanadi. | Xabar modeli texnik qaror sifatida tayyor bo'ladi. |

### Muhim qaror

`SystemLogs` hech qachon asosiy business flow'ning yagona failure point'i bo'lmasin. Ya'ni log yozish muvaffaqiyatsiz bo'lsa ham, agar biznes action to'g'ri bajarilgan bo'lsa, system butunlay yiqilmasligi yaxshiroq.

---

## 6-Bosqich: Bot'ni ORM'dan Ajratish

Hozir bot to'g'ridan-to'g'ri Django ORM bilan ishlayapti. Bu local MVP uchun bo'lishi mumkin, lekin uzoq muddat uchun yaxshi arxitektura emas.

## To'g'ri yo'nalish

Bot 2 xil yo'ldan biriga o'tishi kerak:

1. API orqali ishlash.
2. Yoki service layer orqali ishlash.

Eng toza variant: bot API bilan gaplashsin.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| API client'ni ishga tushirish | `bot/utils/api_client.py` | Kommentda yotgan kodni toza client darajasiga olib chiq. Auth, GET, POST, error handling bo'lsin. | Bot backend'dan mustaqilroq bo'ladi. | Bot API orqali ma'lumot oladi. |
| Bot handler'larni ingichkalashtirish | `bot/handlers/books.py`, `bot/handlers/users.py`, `bot/handlers/start.py` | ORM query'larni kamaytir, API response bilan ishlaydigan handlerlar yoz. | Bot qatlami presentation layer bo'lib qoladi. | Handlerlar soddalashadi. |
| User registration flow'ni xavfsiz qilish | `bot/handlers/start.py` | Contact yuborgan odamning raqami va user identity tekshiruvini qat'iy qil. | Boshqa odamning raqami bilan ro'yxatdan o'tish holatini yopadi. | Bot registration xavfsiz bo'ladi. |
| Bot state va xatolarni yaxshilash | `bot/handlers/books.py`, `bot/keyboards/*` | Orqaga qaytish, cancel, error message, duplicate request kabi holatlarni yaxshiroq boshqar. | UX va support yukini kamaytiradi. | Bot flow foydalanuvchi uchun silliq ishlaydi. |

### Qayerga nima yozish kerak

`bot/utils/api_client.py` ichida:

- base URL
- auth header
- timeout
- status code handling
- response parse
- exception logikasi

`bot/handlers/books.py` ichida:

- category list
- author list
- book list
- loan request
- current loans

Bu narsalar ORM query bo'lib emas, API client method chaqiruvlari bo'lib yozilishi kerak.

---

## 7-Bosqich: Serializer va View Layer'ni Tozalash

Service layer paydo bo'lgach, serializer va view'larni soddalashtirish kerak.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Serializer'larni oriq qilish | `apps/books/serializers.py`, `apps/users/serializers.py`, `apps/loans/serializers.py` | Serializer ichida asosan validation va representation qoldir. Business action kamaytir. | DRF qatlamlari tushunarli bo'ladi. | Serializer ichida "hamma narsa" qolmaydi. |
| Queryset optimizatsiyasi | `apps/books/views.py`, `apps/loans/views.py`, `apps/users/views.py` | `select_related`, `prefetch_related`, role-based filteringni standart qil. | Performance va permission birga ishlaydi. | API list endpointlar ortiqcha query qilmaydi. |
| Tag va schema'ni tartibga keltirish | `config/settings.py`, view fayllari | Swagger tag nomlarini bir xil standartga olib kel. | API docs professional ko'rinadi. | Schema o'qilishi oson bo'ladi. |

---

## 8-Bosqich: Test Qatlami Yaratish

Test yo'q loyiha hech qachon "zo'r" bo'la olmaydi. Ayniqsa CRM, loan va fine kabi biznes mantiqli tizimda.

## Birinchi bo'lib qaysi testlarni yozish kerak

### Tavsiya etilgan papkalar

- `apps/users/tests/test_auth_api.py`
- `apps/users/tests/test_permissions.py`
- `apps/books/tests/test_books_api.py`
- `apps/loans/tests/test_loan_services.py`
- `apps/loans/tests/test_loan_api.py`
- `apps/loans/tests/test_fine_flow.py`
- `apps/loans/tests/test_waitlist_flow.py`

### Nimalarni test qilish shart

| Test turi | Qaysi faylga yozish kerak | Nima tekshiriladi | Nima uchun kerak |
|---|---|---|---|
| Auth test | `apps/users/tests/test_auth_api.py` | user registration, phone login, blocked user holati | Kirish tizimi ishonchli bo'lishi kerak |
| Permission test | `apps/users/tests/test_permissions.py` | oddiy user vs admin access | Security regression bo'lmasligi uchun |
| Loan service test | `apps/loans/tests/test_loan_services.py` | duplicate request, available copy, blocked user, approval, return | Eng muhim biznes mantiq shu yerda |
| Fine flow test | `apps/loans/tests/test_fine_flow.py` | kechikish, fine yaratish, balance update, pay flow | Moliyaviy hisob xato bo'lmasligi uchun |
| API test | `apps/books/tests/test_books_api.py`, `apps/loans/tests/test_loan_api.py` | endpoint response va permission | Frontend/bot uchun contract barqaror bo'ladi |

### Nega testlar shu tartibda yoziladi

Avval service va permission test yoziladi, chunki ular buzilsa butun tizim buziladi. UI yoki bot testi keyin ham yozsa bo'ladi.

---

## 9-Bosqich: Model va Ma'lumotlar Qatlamini Mustahkamlash

Bu bosqichda ma'lumotlarni DB darajasida ham himoyalash kerak.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Unique va constraint'larni ko'rib chiqish | `apps/users/models.py`, `apps/loans/models.py`, `apps/books/models.py` | Qaysi joyda unique, qaysi joyda composite constraint kerakligini aniqlab yoz. | Faqat application logic'ga tayanib qolmaslik uchun. | DB darajasida ham himoya paydo bo'ladi. |
| Waitlist qoidalarini DB bilan mustahkamlash | `apps/loans/models.py` | Bir user bir book uchun aktiv waitlist qayta yarata olmasligi kerakmi, qaror qil va constraint qo'y. | Duplicate navbatlarni oldini oladi. | Navbat ma'lumotlari toza bo'ladi. |
| Loan state modelini aniqlashtirish | `apps/loans/models.py` | `PENDING -> BORROWED -> RETURNED` kabi status flow qoidalarini model comment yoki service orqali qat'iy qil. | Domen aniq bo'ladi. | Status transition boshqariladigan bo'ladi. |

---

## 10-Bosqich: Admin Panel'ni Professional Qilish

Admin panel bu CRM loyihada juda katta kuch. Uni oddiy CRUD emas, operatsion panelga aylantirish kerak.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Loan approval admin flow'ni service bilan bog'lash | `apps/loans/admin.py` | Admin action ichida to'g'ridan-to'g'ri state o'zgartirish emas, service call bo'lsin. | Admin oqimi va API oqimi bir xil ishlaydi. | Har ikki joyda bitta biznes mantiq ishlaydi. |
| Readonly audit modeli | `apps/loans/admin.py` | `SystemLogs` uchun add/change/delete siyosatini qat'iy belgilab chiq. | Audit yozuvlari ishonchli bo'lishi kerak. | Loglar faqat ko'riladi. |
| Search va filter'larni boyitish | `apps/books/admin.py`, `apps/users/admin.py`, `apps/loans/admin.py` | Eng ko'p ishlatiladigan operational filter'larni qo'sh. | Admin tez ishlaydi. | Kutubxonachi uchun panel qulaylashadi. |

### Yaxshi admin panel nimani beradi

- support ishlari tezlashadi
- kutubxonachi API bilmasa ham tizimdan foydalana oladi
- xatoliklarni qayta tiklash osonlashadi

---

## 11-Bosqich: API Kontraktini Chiroyli Qilish

API professional ko'rinishi uchun faqat ishlashi yetmaydi. Uning response stili ham barqaror bo'lishi kerak.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Error response stilini bir xillash | serializer/view qatlamlari | Validation va business error'lar bir xil formatda qaytsin. | Bot va frontend uchun ishlash oson bo'ladi. | Error parsing sodda bo'ladi. |
| Endpoint naming'ni standart qilish | `apps/*/urls.py`, viewset action'lari | `return_book`, `pay`, `me` kabi action'lar bir xil naming usulida bo'lsin. | API ichki madaniyati yaxshilanadi. | API docs aniq bo'ladi. |
| Swagger tavsifini to'ldirish | `config/settings.py`, views | Har muhim endpoint uchun maqsad, request va response qisqa yozilsin. | API bilan ishlash ancha qulaylashadi. | Swagger foydalanishga tayyor bo'ladi. |

---

## 12-Bosqich: Production Tayyorlov

Bu bosqichni core stabil bo'lmasdan oldin boshlama.

| Vazifa | Qaysi fayl(lar) | Nima yozish yoki o'zgartirish kerak | Nima uchun kerak | Tugallangan holat |
|---|---|---|---|---|
| Production settings | `config/settings.py` | secure cookies, SSL redirect, host validation, static/media strategy | Internetga ochilganda tizim xavfsiz bo'ladi | Production config tayyor bo'ladi |
| Logging strategy | Django settings va server config | app log, error log, bot log ajrat | Support va monitoring uchun | Xatolar izlanadigan bo'ladi |
| Gunicorn/Nginx yoki Docker tayyorlash | yangi infra fayllari | deploy standarti tanla | Bir xil muhitda deploy qilish osonlashadi | Reproducible deploy bo'ladi |
| PostgreSQL'ga to'liq o'tish | settings va deployment | production DB sifatida faqat PostgreSQL ishlat | SQLite production uchun mos emas | Barqaror DB qatlami paydo bo'ladi |

### Keyin qo'shish mumkin bo'lgan narsalar

- Celery orqali reminder job
- overdue notification cron
- analytics dashboard
- reservation expiry
- barcode yoki QR oqimi

Lekin bularni faqat core system ishonchli bo'lgandan keyin qil.

---

## 13-Bosqich: Tavsiya etilgan Papka Tuzilishi

Quyidagi struktura loyihani uzoq muddat yaxshiroq ushlab turishga yordam beradi:

```text
apps/
  users/
    models.py
    serializers.py
    permissions.py
    views.py
    urls.py
    tests/
      test_auth_api.py
      test_permissions.py
  books/
    models.py
    serializers.py
    filters.py
    views.py
    urls.py
    tests/
      test_books_api.py
  loans/
    models.py
    serializers.py
    views.py
    urls.py
    admin.py
    services.py
    utils.py
    tests/
      test_loan_services.py
      test_loan_api.py
      test_fine_flow.py
      test_waitlist_flow.py
bot/
  config.py
  utils/
    api_client.py
  handlers/
    start.py
    books.py
    users.py
config/
  settings.py
  urls.py
README.md
LOYIHA_YAXSHILASH_REJASI.md
```

---

## 14-Bosqich: Amaliy Ish Tartibi

Quyidagi tartib eng samarali:

1. `requirements.txt`, `README.md`, `.env.example`, `config/settings.py` ni to'g'rila.
2. `apps/users/permissions.py`, `apps/users/views.py`, `apps/users/serializers.py` ni to'g'rila.
3. `apps/books/views.py` va `apps/loans/views.py` permissionlarini to'g'rila.
4. `apps/loans/services.py` yarat va loan/fine logic'ni shu yerga ko'chir.
5. `apps/loans/serializers.py`, `apps/loans/admin.py`, `apps/loans/utils.py` ni service layer'ga moslashtir.
6. `bot/utils/api_client.py` ni ishga tushir va handlerlarni ORM'dan ajrat.
7. Test papkalarini ochib, avval permission va loan service test yoz.
8. Keyin fine, waitlist va API testlarini yoz.
9. Oxirida production configuration va deploy hujjatini tayyorla.

## Nega bu tartib eng yaxshi

Chunki:

- avval foundation tuzatiladi
- keyin xavfsizlik yopiladi
- keyin core business flow mustahkamlanadi
- keyin integratsiya soddalashadi
- oxirida test va deploy qo'shiladi

Bu ketma-ketlik qayta ishlash xarajatini kamaytiradi.

---

## 15-Bosqich: "Zo'r loyiha" uchun Definition of Done

Loyiha quyidagi holatga kelsa, uni ancha kuchli darajaga chiqdi deb hisoblash mumkin:

- oddiy user boshqa userni update qila olmaydi
- public registration orqali admin role olib bo'lmaydi
- fine hisobi bir xil qoidaga tayangan
- bitta copy ikki marta faol loan'ga tushmaydi
- loan approve, return va fine pay oqimlari test bilan yopilgan
- bot API orqali ishlaydi
- `manage.py test` nol emas, real testlar ishlaydi
- README yangi odamga yetarli
- settings local va production uchun ajratilgan
- admin panel operatsion ishga mos

---

## 16-Bosqich: Hozirdanoq Qilmaslik Kerak Bo'lgan Ishlar

Quyidagilarni hozir boshlama:

- yangi chiroyli frontend
- analytics sahifalari
- Celery'ni chuqur qo'shish
- Docker'ni birinchi kundan ideal qilish
- ortiqcha refactor

Sababi: core system hali to'liq ishonchli emas. Avval asosi mustahkam bo'lsin.

---

## Xulosa

Bu loyiha potentsial jihatdan yaxshi. Uni zo'r qilishning siri yangi feature qo'shishda emas, balki mavjud struktura ichida quyidagi uchta narsani to'g'ri qilishda:

1. access control
2. core business logic
3. testlangan servis qatlam

Agar shu uchta narsa to'g'ri qilinsa, keyin bot, admin, notification va deploy qatlamlari juda tez professional ko'rinishga keladi.

Eng muhim tavsiya:

`loan` domenini service layer'ga olib chiqishing va permission qatlamini qat'iy qilishing bu loyihaning eng katta o'sish nuqtasi bo'ladi.
