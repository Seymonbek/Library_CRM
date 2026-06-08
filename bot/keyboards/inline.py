from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:
    """
    Kategoriyalar ro'yxati — har biri tugma.
    """
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat["name"], callback_data=f"cat_{cat['id']}")
    builder.adjust(2)
    return builder.as_markup()


def books_carousel_keyboard(
    book: dict,
    book_index: int,
    total_books: int,
    category_id: int,
) -> InlineKeyboardMarkup:
    """
    Kitob carousel — oldingi/keyingi, ijaraga olish, orqaga tugmalari.
    """
    builder = InlineKeyboardBuilder()

    # Navigatsiya tugmalari
    nav_buttons = []
    if book_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"book_{category_id}_{book_index - 1}")
        )
    if book_index < total_books - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"book_{category_id}_{book_index + 1}")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    # Ijaraga olish yoki navbatga turish
    available = book.get("available_copies", 0)
    if available > 0:
        builder.row(InlineKeyboardButton(
            text="🛒 Ijaraga olish",
            callback_data=f"order_{book['id']}"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="📋 Navbatga turish",
            callback_data=f"waitlist_{book['id']}"
        ))

    # Batafsil ma'lumot
    builder.row(InlineKeyboardButton(
        text="ℹ️ Batafsil",
        callback_data=f"detail_{book['id']}"
    ))

    # Orqaga
    builder.row(InlineKeyboardButton(text="↩️ Kategoriyalarga qaytish", callback_data="back_categories"))

    return builder.as_markup()


def profile_actions_keyboard() -> InlineKeyboardMarkup:
    """Profil bo'limidagi amallar."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Ismni o'zgartirish", callback_data="edit_first_name"))
    builder.row(InlineKeyboardButton(text="✏️ Familiyani o'zgartirish", callback_data="edit_last_name"))
    return builder.as_markup()


def loan_detail_keyboard(loan_id: int, status: str) -> InlineKeyboardMarkup:
    """Ijara uchun amallar tugmasi."""
    builder = InlineKeyboardBuilder()

    if status in ("borrowed", "overdue"):
        builder.row(InlineKeyboardButton(
            text="📋 Qaytarish so'rovi",
            callback_data=f"return_info_{loan_id}"
        ))

    builder.row(InlineKeyboardButton(text="↩️ Orqaga", callback_data="back_loans"))
    return builder.as_markup()


def search_results_keyboard(books: list[dict]) -> InlineKeyboardMarkup:
    """Qidiruv natijalari — har bir kitob tugma."""
    builder = InlineKeyboardBuilder()
    for book in books[:10]:  # Maksimum 10 ta natija
        title = book.get("title", "")[:30]
        available = book.get("available_copies", 0)
        emoji = "✅" if available > 0 else "❌"
        builder.row(InlineKeyboardButton(
            text=f"{emoji} {title}",
            callback_data=f"search_book_{book['id']}"
        ))
    return builder.as_markup()
