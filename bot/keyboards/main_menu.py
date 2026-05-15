from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup

def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.button(text="Kitoblar")
    builder.button(text="Mening ijaralarim")
    builder.button(text="Balans va Jarimalar")
    builder.button(text="Profil")

    builder.adjust(2)

    return builder.as_markup(resize_keyboard=True)