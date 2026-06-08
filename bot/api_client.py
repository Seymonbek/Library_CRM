"""
API Client — Django REST API bilan HTTP orqali muloqot.

Nima uchun HTTP client ishlatamiz?
- Bot va API alohida service'lar (microservice arxitekturasi)
- Bot API'dagi permission, validation, throttling'dan foydalanadi
- Kelajakda Docker'da alohida container bo'ladi
- Testlash osonlashadi (mock qilish mumkin)

Har bir method API'ga HTTP so'rov yuboradi va JSON response qaytaradi.
"""

import aiohttp
from bot.config import API_BASE_URL


class APIClient:
    """
    Asinxron HTTP client — API bilan ishlash uchun.

    Token orqali autentifikatsiya qilinadi.
    Har bir bot foydalanuvchisi uchun alohida token saqlanadi.
    """

    def __init__(self, token: str | None = None):
        self.base_url = API_BASE_URL
        self.token = token

    @property
    def _headers(self) -> dict:
        """Authorization header tayyorlash."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get(self, endpoint: str, params: dict | None = None) -> tuple[dict | list, int]:
        """
        GET so'rov yuborish.

        Args:
            endpoint: API endpoint (masalan: "/books/books/")
            params: Query parametrlar (masalan: {"page": 1})

        Returns:
            tuple: (response_data, status_code)
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}{endpoint}",
                headers=self._headers,
                params=params,
            ) as resp:
                data = await resp.json()
                return data, resp.status

    async def post(self, endpoint: str, data: dict | None = None) -> tuple[dict, int]:
        """
        POST so'rov yuborish.

        Args:
            endpoint: API endpoint
            data: Yuborilayotgan JSON data

        Returns:
            tuple: (response_data, status_code)
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}{endpoint}",
                headers=self._headers,
                json=data,
            ) as resp:
                response_data = await resp.json()
                return response_data, resp.status

    async def patch(self, endpoint: str, data: dict | None = None) -> tuple[dict, int]:
        """PATCH so'rov — qisman yangilash uchun."""
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}{endpoint}",
                headers=self._headers,
                json=data,
            ) as resp:
                response_data = await resp.json()
                return response_data, resp.status

    # ──── AUTH ────────────────────────────────────────────────

    async def telegram_register(self, telegram_id: int, phone_number: str, first_name: str, last_name: str) -> tuple[dict, int]:
        """Telegram orqali ro'yxatdan o'tish (parolsiz)."""
        return await self.post("/auth/telegram/register/", {
            "telegram_id": telegram_id,
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name,
        })

    async def telegram_login(self, telegram_id: int) -> tuple[dict, int]:
        """Telegram orqali login (parolsiz) — telegram_id bo'yicha."""
        return await self.post("/auth/telegram/login/", {
            "telegram_id": telegram_id,
        })

    async def register(self, phone_number: str, first_name: str, last_name: str, password: str) -> tuple[dict, int]:
        """Yangi foydalanuvchi ro'yxatdan o'tkazish (web — parol bilan)."""
        return await self.post("/auth/users/", {
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        })

    async def login(self, phone_number: str, password: str) -> tuple[dict, int]:
        """Login — JWT token olish (web — parol bilan)."""
        return await self.post("/auth/login/", {
            "phone_number": phone_number,
            "password": password,
        })

    async def refresh_token(self, refresh: str) -> tuple[dict, int]:
        """Access token yangilash."""
        return await self.post("/auth/token/refresh/", {
            "refresh": refresh,
        })

    async def get_me(self) -> tuple[dict, int]:
        """Joriy foydalanuvchi profilini olish."""
        return await self.get("/auth/users/me/")

    # ──── BOOKS ───────────────────────────────────────────────

    async def get_categories(self) -> tuple[dict, int]:
        """Barcha kategoriyalarni olish."""
        return await self.get("/books/categories/")

    async def get_authors(self, params: dict | None = None) -> tuple[dict, int]:
        """Mualliflar ro'yxatini olish."""
        return await self.get("/books/authors/", params=params)

    async def get_books(self, params: dict | None = None) -> tuple[dict, int]:
        """Kitoblar ro'yxatini olish (filtrlash mumkin)."""
        return await self.get("/books/books/", params=params)

    async def get_book_detail(self, book_id: int) -> tuple[dict, int]:
        """Bitta kitob haqida to'liq ma'lumot."""
        return await self.get(f"/books/books/{book_id}/")

    # ──── LOANS ───────────────────────────────────────────────

    async def create_loan(self, book_id: int, requested_days: int, notes: str = "") -> tuple[dict, int]:
        """Kitob ijaraga olish so'rovi yuborish."""
        return await self.post("/loans/loans/", {
            "book_id": book_id,
            "requested_days": requested_days,
            "notes": notes,
        })

    async def get_my_loans(self) -> tuple[dict, int]:
        """Foydalanuvchining ijaralari."""
        return await self.get("/loans/loans/")

    # ──── FINES ───────────────────────────────────────────────

    async def get_my_fines(self) -> tuple[dict, int]:
        """Foydalanuvchining jarimalari."""
        return await self.get("/loans/fines/")

    # ──── WAITLIST ────────────────────────────────────────────

    async def create_waitlist(self, book_id: int) -> tuple[dict, int]:
        """Navbatga turish."""
        return await self.post("/loans/waitlists/", {
            "book_id": book_id,
        })

    async def get_my_waitlists(self) -> tuple[dict, int]:
        """Foydalanuvchining navbatlari."""
        return await self.get("/loans/waitlists/")

    # ──── ADMIN OPERATIONS ────────────────────────────────────

    async def get_pending_loans(self) -> tuple[dict, int]:
        """Barcha pending (kutilayotgan) ijaralarni olish."""
        return await self.get("/loans/loans/", params={"status": "pending"})

    async def get_all_loans(self, params: dict | None = None) -> tuple[dict, int]:
        """Barcha ijaralar (admin uchun)."""
        return await self.get("/loans/loans/", params=params)

    async def approve_loan(self, loan_id: int) -> tuple[dict, int]:
        """Ijara so'rovini tasdiqlash."""
        return await self.post(f"/loans/loans/{loan_id}/approve/")

    async def return_book(self, loan_id: int, notes: str = "") -> tuple[dict, int]:
        """Kitob qaytarishni qabul qilish."""
        return await self.post(f"/loans/loans/{loan_id}/return_book/", {"notes": notes})

    async def get_all_users(self, params: dict | None = None) -> tuple[dict, int]:
        """Barcha foydalanuvchilar (admin uchun)."""
        return await self.get("/auth/users/", params=params)

    async def get_user_detail(self, user_id: int) -> tuple[dict, int]:
        """Foydalanuvchi batafsil."""
        return await self.get(f"/auth/users/{user_id}/")

    async def update_user(self, user_id: int, data: dict) -> tuple[dict, int]:
        """Foydalanuvchini yangilash (admin)."""
        return await self.patch(f"/auth/users/{user_id}/", data)

    async def get_all_fines(self, params: dict | None = None) -> tuple[dict, int]:
        """Barcha jarimalar (admin uchun)."""
        return await self.get("/loans/fines/", params=params)

    async def pay_fine(self, fine_id: int) -> tuple[dict, int]:
        """Jarima to'lash (admin)."""
        return await self.post(f"/loans/fines/{fine_id}/pay/")

    async def get_borrowed_loans(self) -> tuple[dict, int]:
        """Ijaradagi kitoblar."""
        return await self.get("/loans/loans/", params={"status": "borrowed"})
