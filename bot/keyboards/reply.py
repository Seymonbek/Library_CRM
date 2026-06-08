from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    """Asosiy menyu — 6 ta tugma, 2x3 grid."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📚 Kitoblar")
    builder.button(text="🔍 Qidirish")
    builder.button(text="📖 Mening ijaralarim")
    builder.button(text="📋 Navbatlarim")
    builder.button(text="💰 Balans va Jarimalar")
    builder.button(text="👤 Profil")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def phone_share_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqam yuborish tugmasi."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Telefon raqamni yuborish", request_contact=True)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi — FSM jarayonlarida."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)
