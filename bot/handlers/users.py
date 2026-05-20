from aiogram import types, F, Router
from asgiref.sync import sync_to_async

from apps.users.models import User

router = Router()
@router.message(F.text == "Profil")
async def show_profile(message: types.Message):
    tg_id = message.from_user.id
    user = await User.objects.filter(telegram_id=tg_id).afirst()

    if not user:
        return await message.answer("Profil topilmadi. Qayta /start bosing.")

    text = (
        f"<b>👤 Sizning profilingiz:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Ism: {user.first_name}\n"
        f"📋 Familiya: {user.last_name}\n"
        f"📞 Telefon: {user.phone_number}\n"
        f"🎭 Rol: {user.get_role_display()}\n"
        f"📅 A'zo bo'lingan sana: {user.date_joined.strftime('%d.%m.%Y')}"
    )

    await message.answer(text)

@router.message(F.text == "Balans va Jarimalar")
async def show_balance(message: types.Message):
    tg_id = message.from_user.id
    user = await User.objects.filter(telegram_id=tg_id).afirst()
    if not user:
        return await message.answer("Profil topilmadi.")

    unpaid_fines = await get_unpaid_fines(user)
    text = f"<b>💰 Sizning balansingiz:</b> {user.balance} so'm\n\n"

    if user.balance < 0:
        text += "⚠️ <i>Sizning qarzingiz bor! Iltimos, kutubxonaga kelib to'lov qiling.</i>\n\n"
    else:
        text += "✅ <i>Sizda qarzdorlik yo'q. Baraka toping!</i>\n\n"

    if unpaid_fines:
        text += "<b>Tafsilotlar:</b>\n"
        for fine in unpaid_fines:
            text += f"❌ {fine['amount']} so'm - {fine['reason']}\n"

    await message.answer(text)


@sync_to_async
def get_unpaid_fines(user):
    from apps.loans.models import Fines
    fines = Fines.objects.filter(loan__user=user, is_paid=False)
    return [{
        "amount": f.amount,
        "reason": f.get_reason_display()
    } for f in fines]