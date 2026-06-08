"""
Profile handler — Profil ko'rish, tahrirlash, Balans va Jarimalar.

Funksiyalar:
- 👤 Profil — ma'lumotlar + tahrirlash tugmalari
- ✏️ Ism/Familiya o'zgartirish (FSM)
- 💰 Balans va Jarimalar — to'lanmagan/to'langan

API endpointlar:
- GET /auth/users/me/ — profil
- PATCH /auth/users/{id}/ — profilni yangilash
- GET /loans/fines/ — jarimalar
"""

import logging

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext

from bot.api_client import APIClient
from bot.keyboards.inline import profile_actions_keyboard
from bot.keyboards.reply import main_menu, cancel_keyboard
from bot.states.registration import EditProfileState
from bot.utils.formatting import safe, format_fine_reason

router = Router()
logger = logging.getLogger(__name__)


# ──── PROFIL KO'RISH ───────────────────────────────────────

@router.message(F.text == "👤 Profil")
async def show_profile(message: types.Message, api_client: APIClient | None, bot: Bot):
    """Foydalanuvchi profilini ko'rsatish + tahrirlash tugmalari."""
    if not api_client:
        return await message.answer("⚠️ Avval /start bosib tizimga kiring.")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    data, status_code = await api_client.get_me()

    if status_code != 200:
        return await message.answer("❌ Profil ma'lumotlarini yuklashda xatolik.")

    role_map = {
        "user": "📖 Foydalanuvchi",
        "admin": "🔧 Admin",
        "super_admin": "👑 Super Admin",
    }
    role = role_map.get(data.get("role", ""), data.get("role", ""))

    status_map = {
        "active": "🟢 Faol",
        "blocked": "🔴 Bloklangan",
    }
    status = status_map.get(data.get("status", ""), data.get("status", ""))

    balance = data.get("balance", "0.00")
    balance_float = float(balance)
    balance_text = f"💰 {balance_float:,.0f} so'm"
    if balance_float < 0:
        balance_text = f"💸 {balance_float:,.0f} so'm (qarzdorlik)"

    text = (
        f"<b>👤 Sizning profilingiz</b>\n\n"
        f"┌ 🆔 ID: <code>{data.get('id')}</code>\n"
        f"├ 👤 Ism: <b>{safe(data.get('first_name', ''))}</b>\n"
        f"├ 📋 Familiya: <b>{safe(data.get('last_name', ''))}</b>\n"
        f"├ 📞 Telefon: {safe(data.get('phone_number', ''))}\n"
        f"├ 🎭 Rol: {role}\n"
        f"├ 📊 Holat: {status}\n"
        f"├ {balance_text}\n"
        f"└ 📅 A'zo: {data.get('date_joined', '')[:10]}\n\n"
        f"<i>Profilni tahrirlash uchun quyidagi tugmalarni bosing:</i>"
    )

    await message.answer(text, reply_markup=profile_actions_keyboard())


# ──── PROFIL TAHRIRLASH ────────────────────────────────────

@router.callback_query(F.data == "edit_first_name")
async def edit_first_name_start(callback: types.CallbackQuery, state: FSMContext):
    """Ismni o'zgartirish boshlash."""
    await callback.message.answer(
        "✏️ Yangi <b>ismingizni</b> kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(EditProfileState.waiting_for_first_name)
    await callback.answer()


@router.message(EditProfileState.waiting_for_first_name)
async def edit_first_name_process(message: types.Message, state: FSMContext, api_client: APIClient | None):
    """Yangi ismni qabul qilib, API'ga yuborish."""
    if not api_client:
        await state.set_state(None)
        return await message.answer("⚠️ Sessiya tugadi. /start bosing.")

    name = message.text.strip()
    if len(name) < 2 or len(name) > 30:
        return await message.answer("⚠️ Ism 2-30 ta harf orasida bo'lishi kerak:")

    # Avval user ID ni olish
    me_data, me_status = await api_client.get_me()
    if me_status != 200:
        await state.set_state(None)
        return await message.answer("❌ Xatolik yuz berdi.", reply_markup=main_menu())

    user_id = me_data.get("id")
    response, status_code = await api_client.patch(f"/auth/users/{user_id}/", {"first_name": name})

    if status_code == 200:
        await message.answer(
            f"✅ Ismingiz <b>{safe(name)}</b> ga o'zgartirildi!",
            reply_markup=main_menu(),
        )
    else:
        await message.answer("❌ O'zgartirishda xatolik yuz berdi.", reply_markup=main_menu())

    await state.set_state(None)


@router.callback_query(F.data == "edit_last_name")
async def edit_last_name_start(callback: types.CallbackQuery, state: FSMContext):
    """Familiyani o'zgartirish boshlash."""
    await callback.message.answer(
        "✏️ Yangi <b>familiyangizni</b> kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(EditProfileState.waiting_for_last_name)
    await callback.answer()


@router.message(EditProfileState.waiting_for_last_name)
async def edit_last_name_process(message: types.Message, state: FSMContext, api_client: APIClient | None):
    """Yangi familiyani qabul qilib, API'ga yuborish."""
    if not api_client:
        await state.set_state(None)
        return await message.answer("⚠️ Sessiya tugadi. /start bosing.")

    name = message.text.strip()
    if len(name) < 2 or len(name) > 30:
        return await message.answer("⚠️ Familiya 2-30 ta harf orasida bo'lishi kerak:")

    me_data, me_status = await api_client.get_me()
    if me_status != 200:
        await state.set_state(None)
        return await message.answer("❌ Xatolik yuz berdi.", reply_markup=main_menu())

    user_id = me_data.get("id")
    response, status_code = await api_client.patch(f"/auth/users/{user_id}/", {"last_name": name})

    if status_code == 200:
        await message.answer(
            f"✅ Familiyangiz <b>{safe(name)}</b> ga o'zgartirildi!",
            reply_markup=main_menu(),
        )
    else:
        await message.answer("❌ O'zgartirishda xatolik yuz berdi.", reply_markup=main_menu())

    await state.set_state(None)


# ──── BALANS VA JARIMALAR ──────────────────────────────────

@router.message(F.text == "💰 Balans va Jarimalar")
async def show_balance_and_fines(message: types.Message, api_client: APIClient | None, bot: Bot):
    """Balans va jarimalar ko'rsatish."""
    if not api_client:
        return await message.answer("⚠️ Avval /start bosib tizimga kiring.")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Profil va jarimalarni parallel olamiz
    profile_data, profile_status = await api_client.get_me()
    fines_data, fines_status = await api_client.get_my_fines()

    if profile_status != 200:
        return await message.answer("❌ Ma'lumotlarni yuklashda xatolik.")

    text = "<b>💰 Balans va Jarimalar</b>\n\n"

    # Balans
    balance = float(profile_data.get("balance", 0))
    if balance < 0:
        text += f"💸 <b>Balans: {balance:,.0f} so'm</b>\n"
        text += "⚠️ <i>Sizning qarzdorligingiz bor!</i>\n\n"
    elif balance == 0:
        text += "💰 <b>Balans: 0 so'm</b>\n"
        text += "✅ <i>Qarzdorlik yo'q</i>\n\n"
    else:
        text += f"💰 <b>Balans: +{balance:,.0f} so'm</b> ✅\n\n"

    # Jarimalar
    if fines_status == 200:
        fines = fines_data.get("results", [])
        unpaid_fines = [f for f in fines if not f.get("is_paid")]
        paid_fines = [f for f in fines if f.get("is_paid")]

        if unpaid_fines:
            total_unpaid = sum(float(f.get("amount", 0)) for f in unpaid_fines)
            text += f"<b>❌ To'lanmagan jarimalar ({len(unpaid_fines)} ta):</b>\n"
            text += f"   Jami: <b>{total_unpaid:,.0f} so'm</b>\n\n"

            for fine in unpaid_fines:
                reason = format_fine_reason(fine.get("reason", ""))
                amount = float(fine.get("amount", 0))
                created = fine.get("created_at", "")[:10]
                text += f"   • {amount:,.0f} so'm — {reason} ({created})\n"

            text += "\n💡 <i>To'lash uchun kutubxonaga tashrif buyuring.</i>\n"
        else:
            text += "✅ <b>To'lanmagan jarima yo'q!</b>\n"

        if paid_fines:
            total_paid = sum(float(f.get("amount", 0)) for f in paid_fines)
            text += f"\n📊 To'langan: {len(paid_fines)} ta ({total_paid:,.0f} so'm)"

    await message.answer(text)
