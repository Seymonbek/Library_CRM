"""
Admin handler — Bot ichida admin panel.

Faqat admin va super_admin rolga ega foydalanuvchilar uchun.
Admin quyidagilarni qila oladi:
- 📋 Pending so'rovlarni ko'rish va tasdiqlash/rad etish
- 📚 Ijaradagi kitoblarni ko'rish va qaytarishni qabul qilish
- 💰 Jarimalarni ko'rish va to'lash
- 👥 Foydalanuvchilarni ko'rish va boshqarish
- 📊 Statistika

API endpointlar:
- GET /loans/loans/?status=pending — kutilayotgan so'rovlar
- POST /loans/loans/{id}/approve/ — tasdiqlash
- POST /loans/loans/{id}/return_book/ — qaytarish
- GET /loans/fines/ — jarimalar
- POST /loans/fines/{id}/pay/ — to'lash
- GET /auth/users/ — foydalanuvchilar
- PATCH /auth/users/{id}/ — bloklash/aktivlashtirish
"""

import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api_client import APIClient
from bot.keyboards.reply import main_menu
from bot.utils.formatting import safe, format_loan_status

router = Router()
logger = logging.getLogger(__name__)


# ──── ADMIN TEKSHIRUV HELPER ───────────────────────────────

async def _check_admin(api_client: APIClient | None, message_or_callback) -> dict | None:
    """Admin ekanligini tekshirish. Admin bo'lmasa None qaytaradi."""
    if not api_client:
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.answer("Tizimga kiring", show_alert=True)
        else:
            await message_or_callback.answer("⚠️ Avval /start bosib tizimga kiring.")
        return None

    user_data, status = await api_client.get_me()
    if status != 200:
        return None

    role = user_data.get("role", "")
    if role not in ("admin", "super_admin"):
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.answer("⛔ Sizda admin huquqi yo'q", show_alert=True)
        else:
            await message_or_callback.answer("⛔ Bu bo'lim faqat adminlar uchun.")
        return None

    return user_data


# ──── ADMIN MENU ───────────────────────────────────────────

def admin_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Admin asosiy menyu."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📋 Pending so'rovlar", callback_data="admin_pending"))
    builder.row(types.InlineKeyboardButton(text="📚 Ijaradagi kitoblar", callback_data="admin_borrowed"))
    builder.row(types.InlineKeyboardButton(text="💰 To'lanmagan jarimalar", callback_data="admin_fines"))
    builder.row(types.InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"))
    builder.row(types.InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"))
    return builder.as_markup()


@router.message(Command("admin"))
async def cmd_admin(message: types.Message, api_client: APIClient | None):
    """Admin panel — /admin komandasi."""
    user = await _check_admin(api_client, message)
    if not user:
        return

    await message.answer(
        f"🔧 <b>Admin Panel</b>\n\n"
        f"Xush kelibsiz, {safe(user.get('first_name', 'Admin'))}!\n"
        f"Quyidagi bo'limlardan birini tanlang:",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(F.data == "admin_menu")
async def back_to_admin_menu(callback: types.CallbackQuery, api_client: APIClient | None):
    """Admin menuga qaytish."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    await callback.message.edit_text(
        f"🔧 <b>Admin Panel</b>\n\nBo'limni tanlang:",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════
# PENDING SO'ROVLAR — TASDIQLASH / RAD ETISH
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_pending")
async def show_pending_loans(callback: types.CallbackQuery, api_client: APIClient | None):
    """Pending so'rovlar ro'yxati."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    data, status_code = await api_client.get_pending_loans()
    if status_code != 200:
        return await callback.answer("Xatolik", show_alert=True)

    loans = data.get("results", [])

    if not loans:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="↩️ Orqaga", callback_data="admin_menu"))
        await callback.message.edit_text(
            "✅ <b>Kutilayotgan so'rovlar yo'q!</b>\n\nBarcha so'rovlar ko'rib chiqilgan.",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        return

    text = f"📋 <b>Kutilayotgan so'rovlar ({len(loans)} ta)</b>\n\n"

    builder = InlineKeyboardBuilder()
    for loan in loans[:10]:  # Maksimum 10 ta
        book_title = loan.get("copy", {}).get("book", {}).get("title", "?")[:25]
        user_name = loan.get("user", {}).get("first_name", "?")
        days = loan.get("copy", {})  # requested_days loan ichida
        loan_id = loan.get("id")

        text += (
            f"📙 <b>{safe(book_title)}</b>\n"
            f"   👤 {safe(user_name)} | 🆔 #{loan_id}\n\n"
        )

        builder.row(
            types.InlineKeyboardButton(text=f"✅ #{loan_id} Tasdiqlash", callback_data=f"approve_{loan_id}"),
            types.InlineKeyboardButton(text=f"❌ #{loan_id} Rad", callback_data=f"reject_{loan_id}"),
        )

    builder.row(types.InlineKeyboardButton(text="↩️ Admin menu", callback_data="admin_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("approve_"))
async def approve_loan(callback: types.CallbackQuery, api_client: APIClient | None):
    """Ijara so'rovini tasdiqlash."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    loan_id = int(callback.data.split("_")[1])
    response, status_code = await api_client.approve_loan(loan_id)

    if status_code == 200:
        book_title = response.get("copy", {}).get("book", {}).get("title", "Kitob")
        due_date = response.get("due_date", "")
        borrower = response.get("user", {}).get("first_name", "")

        await callback.message.answer(
            f"✅ <b>Tasdiqlandi!</b>\n\n"
            f"📖 Kitob: {safe(book_title)}\n"
            f"👤 Oluvchi: {safe(borrower)}\n"
            f"📅 Qaytarish muddati: {due_date}\n"
            f"🆔 Loan: #{loan_id}",
        )
        # Listni yangilash
        await show_pending_loans(callback, api_client)
    else:
        error = response.get("detail", "Noma'lum xatolik")
        if isinstance(error, list):
            error = error[0]
        await callback.answer(f"❌ {error}", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def reject_loan_info(callback: types.CallbackQuery):
    """Rad etish haqida ma'lumot."""
    loan_id = callback.data.split("_")[1]
    await callback.message.answer(
        f"❌ Loan #{loan_id} ni rad etish uchun admin panelga kiring:\n"
        f"<code>/admin</code> → Loans → Status ni o'zgartiring.\n\n"
        f"<i>Kelajakda bot orqali rad etish qo'shiladi.</i>",
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════
# IJARADAGI KITOBLAR — QAYTARISHNI QABUL QILISH
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_borrowed")
async def show_borrowed_loans(callback: types.CallbackQuery, api_client: APIClient | None):
    """Ijaradagi kitoblar ro'yxati."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    data, status_code = await api_client.get_borrowed_loans()
    if status_code != 200:
        return await callback.answer("Xatolik", show_alert=True)

    loans = data.get("results", [])

    if not loans:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="↩️ Orqaga", callback_data="admin_menu"))
        await callback.message.edit_text(
            "📭 <b>Hozir ijaradagi kitob yo'q.</b>",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        return

    text = f"📚 <b>Ijaradagi kitoblar ({len(loans)} ta)</b>\n\n"

    builder = InlineKeyboardBuilder()
    for loan in loans[:10]:
        book_title = loan.get("copy", {}).get("book", {}).get("title", "?")[:20]
        user_name = loan.get("user", {}).get("first_name", "?")
        due_date = loan.get("due_date", "?")
        loan_id = loan.get("id")
        is_overdue = loan.get("is_overdue", False)
        overdue_mark = " ⚠️" if is_overdue else ""

        text += (
            f"📙 <b>{safe(book_title)}</b>{overdue_mark}\n"
            f"   👤 {safe(user_name)} | Muddat: {due_date}\n\n"
        )

        builder.row(types.InlineKeyboardButton(
            text=f"📥 #{loan_id} Qaytarishni qabul qilish",
            callback_data=f"return_{loan_id}",
        ))

    builder.row(types.InlineKeyboardButton(text="↩️ Admin menu", callback_data="admin_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("return_"))
async def return_book(callback: types.CallbackQuery, api_client: APIClient | None):
    """Kitob qaytarishni qabul qilish."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    loan_id = int(callback.data.split("_")[1])
    response, status_code = await api_client.return_book(loan_id, notes="Bot orqali qabul qilindi")

    if status_code == 200:
        book_title = response.get("copy", {}).get("book", {}).get("title", "Kitob")
        returned_date = response.get("returned_date", "")

        text = (
            f"✅ <b>Kitob qabul qilindi!</b>\n\n"
            f"📖 Kitob: {safe(book_title)}\n"
            f"📅 Qaytarilgan sana: {returned_date}\n"
            f"🆔 Loan: #{loan_id}\n"
        )

        # Agar jarima yozilgan bo'lsa
        fines = response.get("fines", [])
        if fines:
            text += f"\n⚠️ Jarima yozildi (kech qaytarish)"

        await callback.message.answer(text)
        # Listni yangilash
        await show_borrowed_loans(callback, api_client)
    else:
        error = response.get("detail", "Noma'lum xatolik")
        if isinstance(error, list):
            error = error[0]
        await callback.answer(f"❌ {error}", show_alert=True)


# ══════════════════════════════════════════════════════════
# JARIMALAR — TO'LASH
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_fines")
async def show_unpaid_fines(callback: types.CallbackQuery, api_client: APIClient | None):
    """To'lanmagan jarimalar."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    data, status_code = await api_client.get_all_fines()
    if status_code != 200:
        return await callback.answer("Xatolik", show_alert=True)

    fines = data.get("results", [])
    unpaid = [f for f in fines if not f.get("is_paid")]

    if not unpaid:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="↩️ Orqaga", callback_data="admin_menu"))
        await callback.message.edit_text(
            "✅ <b>To'lanmagan jarima yo'q!</b>",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        return

    total = sum(float(f.get("amount", 0)) for f in unpaid)
    text = f"💰 <b>To'lanmagan jarimalar ({len(unpaid)} ta)</b>\n"
    text += f"💵 Jami: <b>{total:,.0f} so'm</b>\n\n"

    builder = InlineKeyboardBuilder()
    for fine in unpaid[:10]:
        fine_id = fine.get("id")
        amount = float(fine.get("amount", 0))
        loan_info = fine.get("loan", {})
        user_info = loan_info.get("user", {})
        user_name = user_info.get("first_name", "?")
        reason = fine.get("reason", "")

        text += (
            f"  💸 <b>{amount:,.0f} so'm</b> — {safe(user_name)}\n"
            f"     Sabab: {reason} | 🆔 #{fine_id}\n\n"
        )

        builder.row(types.InlineKeyboardButton(
            text=f"✅ #{fine_id} To'landi ({amount:,.0f})",
            callback_data=f"payfine_{fine_id}",
        ))

    builder.row(types.InlineKeyboardButton(text="↩️ Admin menu", callback_data="admin_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("payfine_"))
async def pay_fine(callback: types.CallbackQuery, api_client: APIClient | None):
    """Jarima to'lash."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    fine_id = int(callback.data.split("_")[1])
    response, status_code = await api_client.pay_fine(fine_id)

    if status_code == 200:
        amount = float(response.get("amount", 0))
        await callback.message.answer(
            f"✅ <b>Jarima to'landi!</b>\n\n"
            f"💰 Summa: {amount:,.0f} so'm\n"
            f"🆔 Fine: #{fine_id}",
        )
        # Listni yangilash
        await show_unpaid_fines(callback, api_client)
    else:
        error = response.get("detail", "Xatolik")
        if isinstance(error, list):
            error = error[0]
        await callback.answer(f"❌ {error}", show_alert=True)


# ══════════════════════════════════════════════════════════
# FOYDALANUVCHILAR
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_users")
async def show_users(callback: types.CallbackQuery, api_client: APIClient | None):
    """Foydalanuvchilar ro'yxati."""
    user = await _check_admin(api_client, callback)
    if not user:
        return

    data, status_code = await api_client.get_all_users()
    if status_code != 200:
        return await callback.answer("Xatolik", show_alert=True)

    users = data.get("results", [])

    text = f"👥 <b>Foydalanuvchilar ({data.get('count', 0)} ta)</b>\n\n"

    builder = InlineKeyboardBuilder()
    for u in users[:15]:
        user_id = u.get("id")
        name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("username", "?")
        role = u.get("role", "user")
        status_val = u.get("status", "active")

        role_emoji = {"user": "👤", "admin": "🔧", "super_admin": "👑"}.get(role, "👤")
        status_emoji = "🟢" if status_val == "active" else "🔴"

        text += f"{status_emoji} {role_emoji} <b>{safe(name)}</b> (ID: {user_id})\n"

        builder.row(types.InlineKeyboardButton(
            text=f"👤 {safe(name)[:20]} — Batafsil",
            callback_data=f"userdetail_{user_id}",
        ))

    builder.row(types.InlineKeyboardButton(text="↩️ Admin menu", callback_data="admin_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("userdetail_"))
async def show_user_detail(callback: types.CallbackQuery, api_client: APIClient | None):
    """Foydalanuvchi batafsil + boshqarish tugmalari."""
    admin = await _check_admin(api_client, callback)
    if not admin:
        return

    user_id = int(callback.data.split("_")[1])
    data, status_code = await api_client.get_user_detail(user_id)

    if status_code != 200:
        return await callback.answer("Foydalanuvchi topilmadi", show_alert=True)

    role_map = {"user": "👤 Foydalanuvchi", "admin": "🔧 Admin", "super_admin": "👑 Super Admin"}
    role = role_map.get(data.get("role", ""), data.get("role", ""))
    status_val = data.get("status", "active")
    status_text = "🟢 Faol" if status_val == "active" else "🔴 Bloklangan"
    balance = float(data.get("balance", 0))

    text = (
        f"<b>👤 Foydalanuvchi #{user_id}</b>\n\n"
        f"📋 Ism: <b>{safe(data.get('first_name', ''))}</b>\n"
        f"📋 Familiya: <b>{safe(data.get('last_name', ''))}</b>\n"
        f"📞 Telefon: {safe(data.get('phone_number', 'Yo`q'))}\n"
        f"🎭 Rol: {role}\n"
        f"📊 Holat: {status_text}\n"
        f"💰 Balans: {balance:,.0f} so'm\n"
        f"📅 A'zo: {data.get('date_joined', '')[:10]}\n"
    )

    builder = InlineKeyboardBuilder()

    # Bloklash / Aktivlashtirish
    if status_val == "active":
        builder.row(types.InlineKeyboardButton(
            text="🔴 Bloklash",
            callback_data=f"block_{user_id}",
        ))
    else:
        builder.row(types.InlineKeyboardButton(
            text="🟢 Aktivlashtirish",
            callback_data=f"unblock_{user_id}",
        ))

    builder.row(types.InlineKeyboardButton(text="↩️ Foydalanuvchilar", callback_data="admin_users"))
    builder.row(types.InlineKeyboardButton(text="↩️ Admin menu", callback_data="admin_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("block_"))
async def block_user(callback: types.CallbackQuery, api_client: APIClient | None):
    """Foydalanuvchini bloklash."""
    admin = await _check_admin(api_client, callback)
    if not admin:
        return

    user_id = int(callback.data.split("_")[1])
    response, status_code = await api_client.update_user(user_id, {"status": "blocked"})

    if status_code == 200:
        name = f"{response.get('first_name', '')} {response.get('last_name', '')}".strip()
        await callback.message.answer(f"🔴 <b>{safe(name)}</b> bloklandi!")
        # Batafsil sahifani yangilash
        callback.data = f"userdetail_{user_id}"
        await show_user_detail(callback, api_client)
    else:
        await callback.answer("❌ Xatolik", show_alert=True)


@router.callback_query(F.data.startswith("unblock_"))
async def unblock_user(callback: types.CallbackQuery, api_client: APIClient | None):
    """Foydalanuvchini aktivlashtirish."""
    admin = await _check_admin(api_client, callback)
    if not admin:
        return

    user_id = int(callback.data.split("_")[1])
    response, status_code = await api_client.update_user(user_id, {"status": "active"})

    if status_code == 200:
        name = f"{response.get('first_name', '')} {response.get('last_name', '')}".strip()
        await callback.message.answer(f"🟢 <b>{safe(name)}</b> aktivlashtirildi!")
        callback.data = f"userdetail_{user_id}"
        await show_user_detail(callback, api_client)
    else:
        await callback.answer("❌ Xatolik", show_alert=True)


# ══════════════════════════════════════════════════════════
# STATISTIKA
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery, api_client: APIClient | None):
    """Umumiy statistika."""
    admin = await _check_admin(api_client, callback)
    if not admin:
        return

    # Parallel so'rovlar
    users_data, _ = await api_client.get_all_users()
    books_data, _ = await api_client.get_books()
    loans_data, _ = await api_client.get_all_loans()
    pending_data, _ = await api_client.get_pending_loans()
    borrowed_data, _ = await api_client.get_borrowed_loans()
    fines_data, _ = await api_client.get_all_fines()

    total_users = users_data.get("count", 0) if isinstance(users_data, dict) else 0
    total_books = books_data.get("count", 0) if isinstance(books_data, dict) else 0
    total_loans = loans_data.get("count", 0) if isinstance(loans_data, dict) else 0
    pending_count = pending_data.get("count", 0) if isinstance(pending_data, dict) else 0
    borrowed_count = borrowed_data.get("count", 0) if isinstance(borrowed_data, dict) else 0

    # Jarimalar
    fines = fines_data.get("results", []) if isinstance(fines_data, dict) else []
    unpaid_fines = [f for f in fines if not f.get("is_paid")]
    total_unpaid = sum(float(f.get("amount", 0)) for f in unpaid_fines)

    text = (
        f"📊 <b>Tizim statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{total_users}</b>\n"
        f"📚 Kitoblar: <b>{total_books}</b>\n"
        f"📖 Jami ijaralar: <b>{total_loans}</b>\n\n"
        f"┌ 🕐 Kutilayotgan: <b>{pending_count}</b>\n"
        f"├ 📖 Ijarada: <b>{borrowed_count}</b>\n"
        f"└ 💰 To'lanmagan jarimalar: <b>{len(unpaid_fines)}</b> ta ({total_unpaid:,.0f} so'm)\n\n"
    )

    if pending_count > 0:
        text += f"⚠️ <i>{pending_count} ta so'rov kutilmoqda!</i>"

    builder = InlineKeyboardBuilder()
    if pending_count > 0:
        builder.row(types.InlineKeyboardButton(text=f"📋 Pending ({pending_count})", callback_data="admin_pending"))
    builder.row(types.InlineKeyboardButton(text="↩️ Admin menu", callback_data="admin_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
