import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from apps.users.models import User
from bot.keyboards.main_menu import main_menu
from bot.keyboards.auth import phone_share_keyboard

router = Router()


# FSM holatlari
class RegisterState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    user = await User.objects.filter(telegram_id=tg_id).afirst()

    if user:
        await message.answer(f"Xush kelibsiz, {user.first_name}!", reply_markup=main_menu())
    else:
        await message.answer(
            "Assalomu alaykum! Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n"
            "Avval telefon raqamingizni yuboring:",
            reply_markup=phone_share_keyboard()
        )
        await state.set_state(RegisterState.waiting_for_phone)


# 1. Telefon raqamini qabul qilish
@router.message(RegisterState.waiting_for_phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Rahmat! Endi ismingizni kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(RegisterState.waiting_for_first_name)


# 2. Ismni qabul qilish
@router.message(RegisterState.waiting_for_first_name)
async def get_first_name(message: types.Message, state: FSMContext):
    if len(message.text) < 2:
        return await message.answer("Ism juda qisqa. Iltimos, to'liq ismingizni yozing:")

    await state.update_data(first_name=message.text)
    await message.answer("Ajoyib! Endi familiyangizni kiriting:")
    await state.set_state(RegisterState.waiting_for_last_name)


# 3. Familiyani qabul qilish va Bazaga saqlash
@router.message(RegisterState.waiting_for_last_name)
async def get_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)

    # Hamma ma'lumotlarni state'dan olamiz
    data = await state.get_data()
    tg_id = message.from_user.id

    try:
        # Django User yaratish
        new_user = User(
            username=f"user_{tg_id}",
            phone_number=data['phone'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            telegram_id=tg_id,
            role=User.Role.USER
        )
        new_user.set_unusable_password()
        await new_user.asave()

        await message.answer(
            f"Tabriklaymiz, {data['first_name']}! Ro'yxatdan o'tdingiz.",
            reply_markup=main_menu()
        )
        await state.clear()  # FSM ni tozalaymiz

    except Exception as e:
        logging.error(f"Error creating user: {e}")
        await message.answer("Xatolik yuz berdi. Qayta urinib ko'ring.")
        await state.clear()