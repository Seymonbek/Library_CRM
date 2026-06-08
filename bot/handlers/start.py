"""
Start handler — /start va registratsiya.

Flow (oddiy foydalanuvchi uchun — parolsiz):
1. /start → telegram_id orqali login urinish
2. Agar user mavjud → token oladi → menyu
3. Agar yo'q → registratsiya: telefon → ism → familiya → tamom!
4. Parol so'ralmaydi — Telegram o'zi autentifikatsiya

Admin/Super Admin uchun:
- /admin komandasi orqali admin panelga kirish
- Web panel uchun parol bilan login (API: /auth/login/)
"""

import logging

from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.api_client import APIClient
from bot.keyboards.reply import main_menu, phone_share_keyboard, cancel_keyboard
from bot.states.registration import RegisterState
from bot.utils.formatting import safe

router = Router()
logger = logging.getLogger(__name__)


# ──── /START ───────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, api_client: APIClient | None, bot: Bot):
    """
    /start — avtomatik auth.
    1. Agar token bor va valid → menyu
    2. Agar yo'q → telegram_id orqali login urinish
    3. Agar user topilmasa → registratsiya boshlash
    """
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # 1. Agar allaqachon token bor
    if api_client:
        user_data, status_code = await api_client.get_me()
        if status_code == 200:
            name = safe(user_data.get("first_name", "Foydalanuvchi"))
            await message.answer(
                f"Xush kelibsiz, <b>{name}</b>! 👋\n\n"
                f"Quyidagi menyu orqali botdan foydalaning:",
                reply_markup=main_menu(),
            )
            return

    # 2. Token yo'q — telegram_id orqali login urinish
    tg_id = message.from_user.id
    client = APIClient()
    response, status_code = await client.telegram_login(telegram_id=tg_id)

    if status_code == 200:
        # User bor — tokenlarni saqlash
        await state.update_data(
            access_token=response.get("access"),
            refresh_token=response.get("refresh"),
        )
        name = safe(response.get("user", {}).get("first_name", "Foydalanuvchi"))
        await message.answer(
            f"Xush kelibsiz, <b>{name}</b>! 👋\n\n"
            f"Quyidagi menyu orqali botdan foydalaning:",
            reply_markup=main_menu(),
        )
        return

    # 3. User topilmadi — registratsiya
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "📚 <b>Kutubxona CRM</b> botiga xush kelibsiz.\n\n"
        "Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n"
        "Bu juda tez — faqat 3 qadam:\n\n"
        "1️⃣ Telefon raqam\n"
        "2️⃣ Ism\n"
        "3️⃣ Familiya\n\n"
        "📱 <b>Telefon raqamingizni yuboring:</b>",
        reply_markup=phone_share_keyboard(),
    )
    await state.set_state(RegisterState.waiting_for_phone)


# ──── BEKOR QILISH ─────────────────────────────────────────

@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: types.Message, state: FSMContext):
    """Har qanday FSM jarayonini bekor qilish."""
    current_state = await state.get_state()
    if current_state is None:
        return await message.answer("Bekor qilinadigan jarayon yo'q.", reply_markup=main_menu())

    await state.set_state(None)
    await message.answer(
        "❌ Bekor qilindi.\n\nQayta boshlash uchun /start bosing.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# ══════════════════════════════════════════════════════════
# REGISTRATSIYA (PAROLSIZ)
# ══════════════════════════════════════════════════════════

@router.message(RegisterState.waiting_for_phone, F.contact)
async def reg_get_phone(message: types.Message, state: FSMContext):
    """Telefon raqamni qabul qilish."""
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    await state.update_data(phone=phone)
    await message.answer(
        "✅ Rahmat!\n\n2️⃣ Endi <b>ismingizni</b> kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(RegisterState.waiting_for_first_name)


@router.message(RegisterState.waiting_for_phone)
async def reg_invalid_phone(message: types.Message):
    """Contact yuborilmasa."""
    await message.answer(
        "⚠️ Iltimos, pastdagi <b>📱 Telefon raqamni yuborish</b> tugmasini bosing.",
        reply_markup=phone_share_keyboard(),
    )


@router.message(RegisterState.waiting_for_first_name)
async def reg_get_first_name(message: types.Message, state: FSMContext):
    """Ism."""
    name = message.text.strip()

    if len(name) < 2:
        return await message.answer("⚠️ Ism kamida 2 ta harf bo'lishi kerak:")
    if len(name) > 30:
        return await message.answer("⚠️ Ism 30 ta harfdan oshmasin:")

    await state.update_data(first_name=name)
    await message.answer("3️⃣ Ajoyib! Endi <b>familiyangizni</b> kiriting:")
    await state.set_state(RegisterState.waiting_for_last_name)


@router.message(RegisterState.waiting_for_last_name)
async def reg_get_last_name_and_register(message: types.Message, state: FSMContext, bot: Bot):
    """Familiya qabul qilib, ro'yxatdan o'tkazish (parolsiz)."""
    name = message.text.strip()

    if len(name) < 2:
        return await message.answer("⚠️ Familiya kamida 2 ta harf bo'lishi kerak:")
    if len(name) > 30:
        return await message.answer("⚠️ Familiya 30 ta harfdan oshmasin:")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    data = await state.get_data()
    tg_id = message.from_user.id

    # API'ga telegram register so'rovi
    client = APIClient()
    response, status_code = await client.telegram_register(
        telegram_id=tg_id,
        phone_number=data["phone"],
        first_name=data["first_name"],
        last_name=name,
    )

    if status_code == 201:
        # Muvaffaqiyatli — tokenlarni saqlash
        tokens = response.get("tokens", {})
        await state.clear()
        await state.update_data(
            access_token=tokens.get("access"),
            refresh_token=tokens.get("refresh"),
        )

        user_name = safe(response.get("user", {}).get("first_name", ""))
        await message.answer(
            f"🎉 <b>Tabriklaymiz, {user_name}!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Ro'yxatdan muvaffaqiyatli o'tdingiz.\n\n"
            f"Endi botdan to'liq foydalanishingiz mumkin.\n"
            f"Quyidagi menyu orqali kitoblarni ko'ring:",
            reply_markup=main_menu(),
        )
        logger.info(f"New user registered via Telegram: {data['phone']} (tg_id: {tg_id})")

    elif status_code == 400:
        error_msg = _format_errors(response)
        await message.answer(
            f"❌ Ro'yxatdan o'tishda xatolik:\n{error_msg}\n\n"
            f"/start — qayta boshlash",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Server xatosi. Keyinroq urinib ko'ring.\n/start — qayta boshlash",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()
        logger.error(f"Registration failed: {status_code} — {response}")


# ──── HELPERS ──────────────────────────────────────────────

def _format_errors(response: dict) -> str:
    """API validation xatolarini formatlash."""
    error_msg = ""
    for field, messages_list in response.items():
        if isinstance(messages_list, list):
            error_msg += f"• {messages_list[0]}\n"
        elif isinstance(messages_list, str):
            error_msg += f"• {messages_list}\n"
        else:
            error_msg += f"• {field}: {messages_list}\n"
    return error_msg.strip()
