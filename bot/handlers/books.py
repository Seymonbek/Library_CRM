import os

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asgiref.sync import sync_to_async
from django.conf import settings

from apps.books.models import Books, Author, Category
from apps.loans.models import Loans
from apps.users.models import User
from apps.loans.serializers import LoanCreateSerializer
from bot.keyboards.main_menu import main_menu

router = Router()


class LoanState(StatesGroup):
    waiting_for_days = State()


# BAZA BILAN ISHLASH

@sync_to_async
def get_categories():
    return list(Category.objects.filter(books__isnull=False).distinct().values('id', 'name'))


@sync_to_async
def get_authors_by_category(category_id):
    authors = Author.objects.filter(books__category_id=category_id).distinct()
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in authors]


@sync_to_async
def get_books_filtered(category_id, author_id):
    books = Books.objects.filter(category_id=category_id, author_id=author_id)
    result = []
    for b in books:
        available_count = b.bookcopies_set.filter(status='on_shelf').count()
        result.append({
            "id": b.id, "title": b.title, "available": available_count,
            "cover": str(b.cover_image) if b.cover_image else None
        })
    return result


@sync_to_async
def create_pending_loan(user, book_id, days):
    data = {"book_id": book_id, "user_id": user.id, "requested_days": days, "notes": f"Bot orqali {days} kunga so'rov."}

    class DummyRequest:
        def __init__(self, u): self.user = u

    serializer = LoanCreateSerializer(data=data, context={'request': DummyRequest(user)})
    if serializer.is_valid():
        serializer.save()
        return True, None
    return False, str(list(serializer.errors.values())[0][0])


@sync_to_async
def get_user_loans_list(user):
    loans = Loans.objects.filter(user=user, status__in=['pending', 'borrowed']).select_related('copy__book')
    return [{
        "title": ln.copy.book.title,
        "status": ln.get_status_display(),
        "due_date": ln.due_date.strftime("%d.%m.%Y") if ln.due_date else "Tasdiqlanishi kutilmoqda"
    } for ln in loans]


# HANDLERLAR

@router.message(F.text == "Kitoblar")
async def show_categories(message: types.Message):
    categories = await get_categories()
    if not categories: return await message.answer("Hozircha kitoblar yo'q")
    builder = InlineKeyboardBuilder()
    for cat in categories: builder.button(text=cat['name'], callback_data=f"cat_{cat['id']}")
    builder.adjust(2)
    await message.answer("<b>📚 Bo'limni tanlang:</b>", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("cat_"))
async def show_authors(callback: types.CallbackQuery):
    category_id = int(callback.data.split("_")[1])
    authors = await get_authors_by_category(category_id)
    builder = InlineKeyboardBuilder()
    for auth in authors: builder.button(text=auth['name'], callback_data=f"auth_{category_id}_{auth['id']}_0")
    builder.button(text="⬅️ Orqaga", callback_data="back_to_main_cat")
    builder.adjust(1)
    await (
        callback.message.delete() if callback.message.photo else callback.message.edit_text("<b>Muallifni tanlang:</b>",
                                                                                            reply_markup=builder.as_markup()))
    if callback.message.photo: await callback.message.answer("<b>Muallifni tanlang:</b>",
                                                             reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("auth_"))
async def show_books_carousel(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    category_id, author_id, book_index = int(parts[1]), int(parts[2]), int(parts[3])
    books_list = await get_books_filtered(category_id, author_id)
    if not books_list: return await callback.answer("Kitob qolmagan")
    if book_index >= len(books_list):
        book_index = len(books_list) - 1
    elif book_index < 0:
        book_index = 0
    current_book = books_list[book_index]
    caption = f"📖 <b>{current_book['title']}</b>\n✅ Mavjud: {current_book['available']} ta\n<i>Kitob {book_index + 1}/{len(books_list)}</i>"

    builder = InlineKeyboardBuilder()
    nav = []
    if book_index > 0: nav.append(
        InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"auth_{category_id}_{author_id}_{book_index - 1}"))
    if book_index < len(books_list) - 1: nav.append(
        InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"auth_{category_id}_{author_id}_{book_index + 1}"))
    builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🛒 Ijaraga olish", callback_data=f"order_{current_book['id']}"))
    builder.row(InlineKeyboardButton(text="↩️ Orqaga", callback_data=f"cat_{category_id}"))

    if current_book['cover']:
        photo = FSInputFile(os.path.join(settings.MEDIA_ROOT, current_book['cover']))
        if callback.message.photo:
            await callback.message.edit_media(media=InputMediaPhoto(media=photo, caption=caption),
                                              reply_markup=builder.as_markup())
        else:
            await callback.message.delete()
            await callback.message.answer_photo(photo=photo, caption=caption, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(caption, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("order_"))
async def start_loan(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(selected_book_id=int(callback.data.split("_")[1]))
    await callback.message.answer("Ushbu kitobni necha kunga olmoqchisiz? (masalan: 10)")
    await state.set_state(LoanState.waiting_for_days)
    await callback.answer()


@router.message(LoanState.waiting_for_days)
async def process_days(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Faqat raqam kiriting!")
    data = await state.get_data()
    user = await User.objects.filter(telegram_id=message.from_user.id).afirst()
    success, error = await create_pending_loan(user, data['selected_book_id'], int(message.text))
    await message.answer(f"✅ So'rov yuborildi!" if success else f"❌ Xatolik: {error}", reply_markup=main_menu())
    await state.clear()


@router.message(F.text == "Mening ijaralarim")
async def show_loans(message: types.Message):
    user = await User.objects.filter(telegram_id=message.from_user.id).afirst()
    loans = await get_user_loans_list(user)
    if not loans: return await message.answer("Faol ijaralar yo'q.")
    text = "<b>📖 Sizning ijaralaringiz:</b>\n\n"
    for l in loans: text += f"📙 <b>{l['title']}</b>\nHolat: {l['status']}\nQaytarish: {l['due_date']}\n\n"
    await message.answer(text)


@router.callback_query(F.data == "back_to_main_cat")
async def back_menu(callback: types.CallbackQuery):
    await show_categories(callback.message)
    await callback.message.delete()