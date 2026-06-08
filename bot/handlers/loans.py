"""
Loans handler — Ijaralar va Navbatlar.

Funksiyalar:
- 📖 Mening ijaralarim — barcha ijaralar ro'yxati
- 📋 Navbatlarim — kitob navbatlari
- Har bir ijara uchun batafsil ma'lumot

API endpointlar:
- GET /loans/loans/ — ijaralar
- GET /loans/waitlists/ — navbatlar
"""

import logging

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext

from bot.api_client import APIClient
from bot.keyboards.inline import loan_detail_keyboard
from bot.keyboards.reply import main_menu
from bot.utils.formatting import safe, format_loan_status

router = Router()
logger = logging.getLogger(__name__)


# ──── MENING IJARALARIM ───────────────────────────────────

@router.message(F.text == "📖 Mening ijaralarim")
async def show_my_loans(message: types.Message, api_client: APIClient | None, bot: Bot):
    """Foydalanuvchining barcha ijaralarini ko'rsatish."""
    if not api_client:
        return await message.answer("⚠️ Avval /start bosib tizimga kiring.")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    data, status_code = await api_client.get_my_loans()

    if status_code != 200:
        return await message.answer("❌ Ijaralarni yuklashda xatolik yuz berdi.")

    loans = data.get("results", [])

    if not loans:
        return await message.answer(
            "📭 <b>Sizda hozircha ijaralar yo'q.</b>\n\n"
            "📚 Kitoblar bo'limidan kitob ijaraga olishingiz mumkin."
        )

    # Ijaralarni statusga qarab guruhlash
    pending = [l for l in loans if l.get("status") == "pending"]
    borrowed = [l for l in loans if l.get("status") == "borrowed"]
    overdue = [l for l in loans if l.get("status") == "overdue"]
    returned = [l for l in loans if l.get("status") == "returned"]

    text = "<b>📖 Sizning ijaralaringiz</b>\n\n"

    if overdue:
        text += "⚠️ <b>MUDDATI O'TGAN:</b>\n"
        for loan in overdue:
            text += _format_loan_item(loan)
        text += "\n"

    if borrowed:
        text += "📖 <b>Ijaradagi kitoblar:</b>\n"
        for loan in borrowed:
            text += _format_loan_item(loan)
        text += "\n"

    if pending:
        text += "🕐 <b>Tasdiqlanishi kutilmoqda:</b>\n"
        for loan in pending:
            text += _format_loan_item(loan)
        text += "\n"

    if returned:
        # Faqat oxirgi 3 tasini ko'rsatamiz
        text += f"✅ <b>Qaytarilgan ({len(returned)} ta):</b>\n"
        for loan in returned[:3]:
            text += _format_loan_item(loan)
        if len(returned) > 3:
            text += f"   <i>... va yana {len(returned) - 3} ta</i>\n"

    # Statistika
    text += f"\n📊 <b>Jami:</b> {len(loans)} ta ijara"
    if overdue:
        text += f" | ⚠️ {len(overdue)} ta muddati o'tgan"

    await message.answer(text)


def _format_loan_item(loan: dict) -> str:
    """Bitta ijara qatorini formatlash."""
    book_info = loan.get("copy", {}).get("book", {})
    title = safe(book_info.get("title", "Nomalum"))
    status = format_loan_status(loan.get("status", ""))
    due_date = loan.get("due_date")

    line = f"   📙 <b>{title}</b>\n"
    line += f"      {status}"

    if due_date:
        line += f" | Muddat: {due_date}"

    is_overdue = loan.get("is_overdue", False)
    if is_overdue:
        line += " ⚠️"

    line += "\n"
    return line


# ──── QAYTARISH HAQIDA MA'LUMOT ────────────────────────────

@router.callback_query(F.data.startswith("return_info_"))
async def return_info(callback: types.CallbackQuery):
    """Kitob qaytarish haqida ma'lumot."""
    await callback.message.answer(
        "📋 <b>Kitob qaytarish</b>\n\n"
        "Kitobni qaytarish uchun kutubxonaga tashrif buyuring.\n"
        "Admin kitobni qabul qilib, tizimda belgilaydi.\n\n"
        "⏰ <i>Muddatidan oldin qaytarsangiz — jarima bo'lmaydi.</i>\n"
        "⚠️ <i>Kech qaytarsangiz — har kunga 2,000 so'm jarima.</i>",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_loans")
async def back_to_loans(callback: types.CallbackQuery, api_client: APIClient | None):
    """Ijaralar ro'yxatiga qaytish."""
    if api_client:
        await show_my_loans(callback.message, api_client)
    await callback.answer()


# ──── NAVBATLARIM ──────────────────────────────────────────

@router.message(F.text == "📋 Navbatlarim")
async def show_my_waitlists(message: types.Message, api_client: APIClient | None, bot: Bot):
    """Foydalanuvchining navbatlarini ko'rsatish."""
    if not api_client:
        return await message.answer("⚠️ Avval /start bosib tizimga kiring.")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    data, status_code = await api_client.get_my_waitlists()

    if status_code != 200:
        return await message.answer("❌ Navbatlarni yuklashda xatolik.")

    waitlists = data.get("results", [])

    if not waitlists:
        return await message.answer(
            "📭 <b>Sizda hozircha navbat yo'q.</b>\n\n"
            "Kitob mavjud bo'lmasa, \"📋 Navbatga turish\" tugmasini bosing — \n"
            "kitob bo'shaganda xabar beramiz."
        )

    text = "<b>📋 Sizning navbatlaringiz</b>\n\n"

    status_emoji = {
        "pending": "🕐 Navbatda",
        "notified": "🔔 Kitob bo'shadi!",
        "fulfilled": "✅ Bajarildi",
        "cancelled": "❌ Bekor qilindi",
    }

    for wl in waitlists:
        book = wl.get("book", {})
        title = safe(book.get("title", "Nomalum"))
        status = status_emoji.get(wl.get("status", ""), wl.get("status", ""))
        created = wl.get("created_at", "")[:10]

        text += f"📖 <b>{title}</b>\n"
        text += f"   {status} | Sana: {created}\n\n"

        # Agar kitob bo'shagan bo'lsa — habar
        if wl.get("status") == "notified":
            text += "   💡 <i>Hozir ijaraga olishingiz mumkin!</i>\n\n"

    await message.answer(text)
