"""
FSM State'lar — barcha ko'p bosqichli dialoglar uchun.
"""

from aiogram.fsm.state import StatesGroup, State


class RegisterState(StatesGroup):
    """
    Ro'yxatdan o'tish (parolsiz):
    1. Telefon raqam (contact button)
    2. Ism
    3. Familiya → keyin avtomatik register
    """
    waiting_for_phone = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()


class LoanState(StatesGroup):
    """Kitob ijaraga olish — kun kiritish."""
    waiting_for_days = State()


class EditProfileState(StatesGroup):
    """Profil tahrirlash."""
    waiting_for_first_name = State()
    waiting_for_last_name = State()


class SearchState(StatesGroup):
    """Kitob qidirish."""
    waiting_for_query = State()
