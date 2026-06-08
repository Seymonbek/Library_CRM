"""
Books handler — Kitoblar, Qidiruv, Carousel, Ijara, Navbat.

Funksiyalar:
- 📚 Kitoblar — kategoriya bo'yicha ko'rish (carousel + rasm)
- 🔍 Qidirish — nom/muallif bo'yicha qidirish
- ℹ️ Batafsil — kitob haqida to'liq ma'lumot
- 🛒 Ijaraga olish — tasdiqlash → necha kun → API
- 📋 Navbatga turish — kitob yo'q bo'lganda
"""

import logging

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api_client import APIClient
from bot.config import API_BASE_URL
from bot.keyboards.inline import categories_keyboard, books_carousel_keyboard, search_results_keyboard
from bot.keyboards.reply import main_menu, cancel_keyboard
from bot.states.registration import LoanState, SearchState
from bot.utils.formatting import safe

router = Router()
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# KATEGORIYALAR
# ══════════════════════════════════════════════════════════

@router.message(F.text == "📚 Kitoblar")
async def show_categories(message: types.Message, api_client: APIClient | None, bot: Bot):
    """Kategoriyalar ro'yxatini ko'rsatish."""
    if not api_client:
        return await message.answer("⚠️ Avval /start bosib tizimga kiring.")

    # Typing action — foydalanuvchi javob kutayotganini biladi
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    data, status_code = await api_client.get_categories()

    if status_code != 200:
        return await message.answer("❌ Kategoriyalarni yuklashda xatolik yuz berdi.")

    categories = data.get("results", [])
    if not categories:
        return await message.answer("📭 Hozircha kategoriyalar mavjud emas.")

    await message.answer(
        "📚 <b>Kitoblar bo'limi</b>\n\n"
        "Quyidagi kategoriyalardan birini tanlang.\n"
        "Tanlagan bo'limingiz kitoblari ko'rsatiladi:",
        reply_markup=categories_keyboard(categories),
    )


@router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: types.CallbackQuery, api_client: APIClient | None):
    """Kategoriyalarga qaytish."""
    if not api_client:
        return await callback.answer("Tizimga kiring", show_alert=True)

    data, status_code = await api_client.get_categories()
    if status_code != 200:
        return await callback.answer("Xatolik", show_alert=True)

    categories = data.get("results", [])
    if not categories:
        return await callback.answer("Kategoriyalar topilmadi", show_alert=True)

    text = "📚 <b>Kitoblar bo'limi</b>\n\nKategoriyani tanlang:"

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=categories_keyboard(categories))
    else:
        try:
            await callback.message.edit_text(text, reply_markup=categories_keyboard(categories))
        except Exception:
            await callback.message.answer(text, reply_markup=categories_keyboard(categories))
    await callback.answer()


# ══════════════════════════════════════════════════════════
# KITOBLAR CAROUSEL (RASM BILAN)
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("cat_"))
async def show_books(callback: types.CallbackQuery, api_client: APIClient | None, state: FSMContext):
    """Kategoriya tanlanganda — kitoblarni carousel ko'rsatish."""
    if not api_client:
        return await callback.answer("Tizimga kiring", show_alert=True)

    category_id = int(callback.data.split("_")[1])
    data, status_code = await api_client.get_books(params={"category": category_id})

    if status_code != 200:
        return await callback.answer("Xatolik yuz berdi", show_alert=True)

    books = data.get("results", [])
    if not books:
        return await callback.answer("Bu bo'limda kitob yo'q", show_alert=True)

    await state.update_data(current_books=books, current_category=category_id)
    await _show_book_at_index(callback.message, books, 0, category_id)
    await callback.answer()


@router.callback_query(F.data.startswith("book_"))
async def navigate_books(callback: types.CallbackQuery, api_client: APIClient | None, state: FSMContext):
    """Carousel navigatsiya."""
    if not api_client:
        return await callback.answer("Tizimga kiring", show_alert=True)

    parts = callback.data.split("_")
    category_id = int(parts[1])
    book_index = int(parts[2])

    state_data = await state.get_data()
    books = state_data.get("current_books", [])

    if not books:
        data, status_code = await api_client.get_books(params={"category": category_id})
        if status_code != 200:
            return await callback.answer("Xatolik", show_alert=True)
        books = data.get("results", [])
        await state.update_data(current_books=books, current_category=category_id)

    if not books:
        return await callback.answer("Kitoblar topilmadi", show_alert=True)

    book_index = max(0, min(book_index, len(books) - 1))
    await _show_book_at_index(callback.message, books, book_index, category_id)
    await callback.answer()


async def _show_book_at_index(message: types.Message, books: list[dict], index: int, category_id: int):
    """Kitobni rasm bilan ko'rsatish (carousel)."""
    book = books[index]
    available = book.get("available_copies", 0)

    if available > 0:
        availability = f"✅ Mavjud: <b>{available}</b> nusxa"
    else:
        availability = "❌ Hozircha barcha nusxalar ijarada"

    caption = (
        f"📖 <b>{safe(book['title'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✍️ Muallif: {safe(book.get('author_name', 'Nomalum'))}\n"
        f"🌐 Til: {_format_language(book.get('language', ''))}\n"
        f"📊 {availability}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <i>{index + 1} / {len(books)}</i>"
    )

    keyboard = books_carousel_keyboard(
        book=book,
        book_index=index,
        total_books=len(books),
        category_id=category_id,
    )

    # Text xabar sifatida ko'rsatamiz (rasmni detail'da ko'rsatamiz)
    if message.photo:
        try:
            await message.edit_caption(caption=caption, reply_markup=keyboard)
            return
        except Exception:
            try:
                await message.delete()
            except Exception:
                pass
            await message.answer(text=caption, reply_markup=keyboard)
    else:
        try:
            await message.edit_text(text=caption, reply_markup=keyboard)
        except Exception:
            try:
                await message.delete()
            except Exception:
                pass
            await message.answer(text=caption, reply_markup=keyboard)


# ══════════════════════════════════════════════════════════
# KITOB BATAFSIL (RASM BILAN)
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("detail_"))
async def show_book_detail(callback: types.CallbackQuery, api_client: APIClient | None, bot: Bot):
    """Kitob haqida to'liq ma'lumot + rasm."""
    if not api_client:
        return await callback.answer("Tizimga kiring", show_alert=True)

    book_id = int(callback.data.split("_")[1])

    await bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    data, status_code = await api_client.get_book_detail(book_id)

    if status_code != 200:
        return await callback.answer("Kitob topilmadi", show_alert=True)

    author = data.get("author", {})
    category = data.get("category", {})
    publisher = data.get("publisher", {})

    text = (
        f"📖 <b>{safe(data.get('title', ''))}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✍️ <b>Muallif:</b> {safe(author.get('first_name', ''))} {safe(author.get('last_name', ''))}\n"
        f"📂 <b>Kategoriya:</b> {safe(category.get('name', '—'))}\n"
        f"🏢 <b>Nashriyot:</b> {safe(publisher.get('name', '—') if publisher else '—')}\n"
        f"🌐 <b>Til:</b> {_format_language(data.get('language', ''))}\n"
        f"📄 <b>Sahifalar:</b> {data.get('page_count') or '—'}\n"
        f"📕 <b>ISBN:</b> <code>{data.get('isbn') or '—'}</code>\n"
    )

    description = data.get("description")
    if description:
        desc_text = safe(description[:300])
        if len(description) > 300:
            desc_text += "..."
        text += f"\n📝 <b>Tavsif:</b>\n<i>{desc_text}</i>\n"

    # Tugmalar
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🛒 Ijaraga olish", callback_data=f"order_{book_id}"
    ))
    builder.row(types.InlineKeyboardButton(
        text="📋 Navbatga turish", callback_data=f"waitlist_{book_id}"
    ))
    builder.row(types.InlineKeyboardButton(
        text="↩️ Orqaga", callback_data="back_categories"
    ))

    # Cover image bor-yo'qligini tekshirish
    cover_image = data.get("cover_image")
    if cover_image:
        try:
            # API'dan rasm URL
            image_url = cover_image if cover_image.startswith("http") else f"{API_BASE_URL.replace('/api/v1', '')}{cover_image}"
            photo = URLInputFile(image_url)
            await callback.message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=builder.as_markup(),
            )
        except Exception as e:
            logger.warning(f"Cover image yuklanmadi: {e}")
            await callback.message.answer(text, reply_markup=builder.as_markup())
    else:
        await callback.message.answer(text, reply_markup=builder.as_markup())

    await callback.answer()


# ══════════════════════════════════════════════════════════
# QIDIRISH
# ══════════════════════════════════════════════════════════

@router.message(F.text == "🔍 Qidirish")
async def start_search(message: types.Message, state: FSMContext, api_client: APIClient | None):
    """Kitob qidirishni boshlash."""
    if not api_client:
        return await message.answer("⚠️ Avval /start bosib tizimga kiring.")

    await message.answer(
        "🔍 <b>Kitob qidirish</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Kitob nomi yoki muallif ismini kiriting:\n\n"
        "<i>Masalan: \"O'tkan kunlar\" yoki \"Abdulla Qodiriy\"</i>",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(SearchState.waiting_for_query)


@router.message(SearchState.waiting_for_query)
async def process_search(message: types.Message, state: FSMContext, api_client: APIClient | None, bot: Bot):
    """Qidiruv natijalarini ko'rsatish."""
    if not api_client:
        await state.set_state(None)
        return await message.answer("⚠️ Sessiya tugadi. /start bosing.")

    query = message.text.strip()
    if len(query) < 2:
        return await message.answer("⚠️ Kamida 2 ta harf kiriting:")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    data, status_code = await api_client.get_books(params={"search": query})

    await state.set_state(None)

    if status_code != 200:
        return await message.answer("❌ Qidiruvda xatolik.", reply_markup=main_menu())

    books = data.get("results", [])

    if not books:
        return await message.answer(
            f"📭 <b>\"{safe(query)}\"</b> bo'yicha natija topilmadi.\n\n"
            f"💡 <i>Maslahat: kitob nomining bir qismini yoki muallif ismini kiriting.</i>",
            reply_markup=main_menu(),
        )

    text = (
        f"🔍 <b>Qidiruv natijalari</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>\"{safe(query)}\"</b> bo'yicha <b>{len(books)}</b> ta natija topildi.\n"
        f"Kitobni tanlang:"
    )

    await message.answer(text, reply_markup=search_results_keyboard(books))


@router.callback_query(F.data.startswith("search_book_"))
async def search_book_selected(callback: types.CallbackQuery, api_client: APIClient | None, bot: Bot):
    """Qidiruv natijasidan kitob tanlash."""
    if not api_client:
        return await callback.answer("Tizimga kiring", show_alert=True)

    book_id = int(callback.data.split("_")[2])

    # detail handler'ga yo'naltiramiz
    callback.data = f"detail_{book_id}"
    await show_book_detail(callback, api_client, bot)


# ══════════════════════════════════════════════════════════
# IJARAGA OLISH (CONFIRM DIALOG BILAN)
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("order_"))
async def confirm_loan(callback: types.CallbackQuery, api_client: APIClient | None, state: FSMContext):
    """Ijaraga olishdan oldin tasdiqlash."""
    if not api_client:
        return await callback.answer("Tizimga kiring", show_alert=True)

    book_id = int(callback.data.split("_")[1])
    await state.update_data(selected_book_id=book_id)

    # Tasdiqlash dialog
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Ha, olmoqchiman", callback_data=f"confirm_order_{book_id}"),
    )
    builder.row(
        types.InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data="cancel_order"),
    )

    await callback.message.answer(
        "🛒 <b>Ijaraga olishni tasdiqlang</b>\n\n"
        "Kitobni ijaraga olishni xohlaysizmi?\n"
        "Agar ha bo'lsa — keyingi qadamda muddat kiritasiz.",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    """Ijara bekor qilish."""
    await state.update_data(selected_book_id=None)
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_order_"))
async def start_loan(callback: types.CallbackQuery, state: FSMContext):
    """Tasdiqlangandan keyin — necha kun?"""
    book_id = int(callback.data.split("_")[2])
    await state.update_data(selected_book_id=book_id)

    await callback.message.edit_text(
        "📅 <b>Necha kunga olmoqchisiz?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Raqam kiriting (1 — 25 kun orasida):\n\n"
        "💡 <i>Masalan: 7</i>",
    )
    await state.set_state(LoanState.waiting_for_days)
    await callback.answer()


@router.message(LoanState.waiting_for_days)
async def process_loan_days(message: types.Message, state: FSMContext, api_client: APIClient | None, bot: Bot):
    """Kun sonini qabul qilib, API'ga loan so'rovi yuborish."""
    if not api_client:
        await state.set_state(None)
        return await message.answer("⚠️ Sessiya tugadi. /start bosing.", reply_markup=main_menu())

    text = message.text.strip()

    if not text.isdigit():
        return await message.answer("⚠️ Faqat raqam kiriting (masalan: <b>7</b>):")

    days = int(text)
    if days < 1:
        return await message.answer("⚠️ Kamida <b>1</b> kun bo'lishi kerak:")
    if days > 30:
        return await message.answer("⚠️ Maksimum <b>30</b> kun. Qaytadan kiriting:")

    data = await state.get_data()
    book_id = data.get("selected_book_id")

    if not book_id:
        await state.set_state(None)
        return await message.answer("❌ Xatolik. Qaytadan kitob tanlang.", reply_markup=main_menu())

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # API'ga so'rov
    response, status_code = await api_client.create_loan(
        book_id=book_id,
        requested_days=days,
        notes=f"Bot orqali {days} kunga so'rov.",
    )

    await state.set_state(None)

    if status_code == 201:
        book_title = response.get("copy", {}).get("book", {}).get("title", "Kitob")
        await message.answer(
            f"✅ <b>So'rov muvaffaqiyatli yuborildi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📖 Kitob: <b>{safe(book_title)}</b>\n"
            f"📅 Muddat: <b>{days}</b> kun\n"
            f"🕐 Holat: Kutilmoqda\n\n"
            f"📌 <b>Keyingi qadamlar:</b>\n"
            f"1. Admin so'rovingizni ko'rib chiqadi\n"
            f"2. Tasdiqlangach sizga xabar beriladi\n"
            f"3. Kutubxonaga kelib kitobni olasiz\n\n"
            f"<i>💡 Holatingizni \"📖 Mening ijaralarim\" bo'limidan kuzating.</i>",
            reply_markup=main_menu(),
        )
    elif status_code == 400:
        error_msg = _format_api_errors(response)
        await message.answer(
            f"❌ <b>So'rov yuborib bo'lmadi</b>\n\n{error_msg}\n\n"
            f"<i>💡 Boshqa kitob tanlab ko'ring.</i>",
            reply_markup=main_menu(),
        )
    else:
        await message.answer("❌ Server xatosi. Keyinroq urinib ko'ring.", reply_markup=main_menu())
        logger.error(f"Loan create failed: {status_code} — {response}")


# ══════════════════════════════════════════════════════════
# NAVBATGA TURISH
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("waitlist_"))
async def join_waitlist(callback: types.CallbackQuery, api_client: APIClient | None):
    """Kitob navbatiga turish."""
    if not api_client:
        return await callback.answer("Tizimga kiring", show_alert=True)

    book_id = int(callback.data.split("_")[1])
    response, status_code = await api_client.create_waitlist(book_id=book_id)

    if status_code == 201:
        book = response.get("book", {})
        title = safe(book.get("title", "Kitob"))
        await callback.message.answer(
            f"✅ <b>Navbatga qo'shildingiz!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📖 Kitob: <b>{title}</b>\n"
            f"🕐 Holat: Navbatda\n\n"
            f"<i>Kitob bo'shaganda sizga xabar beramiz.\n"
            f"Navbatingizni \"📋 Navbatlarim\" bo'limidan ko'ring.</i>",
        )
        await callback.answer()
    elif status_code == 400:
        error_msg = list(response.values())[0]
        if isinstance(error_msg, list):
            error_msg = error_msg[0]
        await callback.answer(f"❌ {error_msg}", show_alert=True)
    else:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


# ──── HELPERS ──────────────────────────────────────────────

def _format_language(lang: str) -> str:
    """Til kodini o'zbekchaga."""
    lang_map = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Ruscha", "en": "🇬🇧 Inglizcha"}
    return lang_map.get(lang, lang)


def _format_api_errors(response: dict) -> str:
    """API xatolarini foydalanuvchiga tushunarli formatlash."""
    error_msg = ""
    for field, msgs in response.items():
        if isinstance(msgs, list):
            error_msg += f"• {msgs[0]}\n"
        elif isinstance(msgs, str):
            error_msg += f"• {msgs}\n"
        else:
            error_msg += f"• {field}: {msgs}\n"
    return error_msg.strip()
