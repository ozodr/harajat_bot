"""
💸 Harajat qo'shish handleri - menyu asosida
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.database import Database

router = Router()
logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    ("🍽️ Ovqatlanish", "d:0"),
    ("🎮 Kompyuter oyinlari", "d:1"),
    ("👔 Kiyinish", "d:2"),
    ("🚗 Yo'l haqqi", "d:3"),
    ("💸 Qarz berish", "d:4"),
    ("🏠 Uy-ro'zg'or", "d:5"),
]


class ExpenseState(StatesGroup):
    waiting_amount = State()
    waiting_category_name = State()
    waiting_edit_amount = State()
    waiting_edit_category_name = State()


def get_start_button() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Menyu")]],
        resize_keyboard=True
    )


def parse_amount(text: str) -> float | None:
    t = text.strip().lower().replace(" ", "").replace(",", ".")
    try:
        if t.endswith("k"):
            return float(t[:-1]) * 1000
        return float(t)
    except ValueError:
        return None


async def build_main_keyboard(db: Database, user_id: int) -> InlineKeyboardMarkup:
    hidden = await db.get_hidden_defaults(user_id)
    custom = await db.get_custom_categories(user_id)

    all_buttons: list[tuple[str, str]] = []
    for name, ref in DEFAULT_CATEGORIES:
        if ref not in hidden:
            all_buttons.append((name, f"cat:{ref}"))
    for cat_id, name in custom:
        all_buttons.append((name, f"cat:c:{cat_id}"))

    rows = []
    for i in range(0, len(all_buttons), 2):
        row = [InlineKeyboardButton(text=all_buttons[i][0], callback_data=all_buttons[i][1])]
        if i + 1 < len(all_buttons):
            row.append(InlineKeyboardButton(text=all_buttons[i + 1][0], callback_data=all_buttons[i + 1][1]))
        rows.append(row)

    rows.append([
        InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="add_category"),
        InlineKeyboardButton(text="⚙️ Boshqarish", callback_data="manage_cats"),
    ])
    rows.append([
        InlineKeyboardButton(text="📊 Bugungi", callback_data="report_daily"),
        InlineKeyboardButton(text="📅 Haftalik", callback_data="report_weekly"),
    ])
    rows.append([
        InlineKeyboardButton(text="🗓️ Oylik", callback_data="report_monthly"),
        InlineKeyboardButton(text="📆 Yillik", callback_data="report_yearly"),
    ])
    rows.append([InlineKeyboardButton(text="✏️ Harajatni o'chirish/o'zgartirish", callback_data="manage_exp")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── /start va /menu ──────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, state: FSMContext):
    await state.clear()
    name = message.from_user.first_name or "Do'stim"
    keyboard = await build_main_keyboard(db, message.from_user.id)
    await message.answer(
        f"👋 Salom, {name}!\n\n💰 <b>Xarajat turini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_start_button()
    )
    await message.answer("📋 Kategoriyalar:", reply_markup=keyboard)


@router.message(Command("menu"))
@router.message(F.text == "🏠 Menyu")
async def cmd_menu(message: Message, db: Database, state: FSMContext):
    await state.clear()
    keyboard = await build_main_keyboard(db, message.from_user.id)
    await message.answer(
        "📋 <b>Xarajat turini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, db: Database, state: FSMContext):
    await state.clear()
    keyboard = await build_main_keyboard(db, callback.from_user.id)
    await callback.message.edit_text(
        "📋 <b>Xarajat turini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# ── Kategoriya tanlash va summa kiritish ─────────────────────────────────────

@router.callback_query(F.data.startswith("cat:"))
async def category_selected(callback: CallbackQuery, db: Database, state: FSMContext):
    ref = callback.data[4:]

    if ref.startswith("d:"):
        idx = int(ref[2:])
        if idx < len(DEFAULT_CATEGORIES):
            category = DEFAULT_CATEGORIES[idx][0]
        else:
            await callback.answer("Xato!", show_alert=True)
            return
    else:
        cat_id = int(ref[2:])
        category = await db.get_custom_category_name(cat_id)
        if not category:
            await callback.answer("Kategoriya topilmadi!", show_alert=True)
            return

    await state.set_state(ExpenseState.waiting_amount)
    await state.update_data(category=category)

    await callback.message.edit_text(
        f"{category}\n\n💵 <b>Summani kiriting:</b>\n<i>(masalan: 50000 yoki 50k)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_main")]
        ])
    )
    await callback.answer()


@router.message(ExpenseState.waiting_amount)
async def handle_amount(message: Message, db: Database, state: FSMContext):
    amount = parse_amount(message.text)

    if amount is None or amount <= 0:
        await message.answer(
            "❌ Noto'g'ri format. Faqat musbat son kiriting.\n<i>Masalan: 50000 yoki 50k</i>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    category = data.get("category", "📦 Boshqa")

    expense_id = await db.add_expense(
        user_id=message.from_user.id,
        amount=amount,
        category=category
    )
    await state.clear()

    keyboard = await build_main_keyboard(db, message.from_user.id)
    await message.answer(
        f"✅ <b>Saqlandi!</b>\n\n{category}\n💵 Summa: <b>{amount:,.0f} so'm</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Bekor qilish", callback_data=f"undo:{expense_id}")]
        ])
    )
    await message.answer("📋 <b>Xarajat turini tanlang:</b>", parse_mode="HTML", reply_markup=keyboard)


# ── Kategoriya qo'shish ───────────────────────────────────────────────────────

@router.callback_query(F.data == "add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ExpenseState.waiting_category_name)
    await callback.message.edit_text(
        "➕ <b>Yangi kategoriya qo'shish</b>\n\nKategoriya nomini kiriting:\n<i>(masalan: 🏋️ Fitness yoki 📚 Kitoblar)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_main")]
        ])
    )
    await callback.answer()


@router.message(ExpenseState.waiting_category_name)
async def handle_category_name(message: Message, db: Database, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Kategoriya nomi kamida 2 ta belgi bo'lsin.")
        return
    if len(name) > 40:
        await message.answer("❌ Kategoriya nomi 40 ta belgidan oshmasin.")
        return

    await db.add_custom_category(message.from_user.id, name)
    await state.clear()

    keyboard = await build_main_keyboard(db, message.from_user.id)
    await message.answer(
        f"✅ <b>'{name}' kategoriyasi qo'shildi!</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ── Kategoriyalarni boshqarish ────────────────────────────────────────────────

async def build_manage_cats_keyboard(db: Database, user_id: int) -> InlineKeyboardMarkup:
    hidden = await db.get_hidden_defaults(user_id)
    custom = await db.get_custom_categories(user_id)

    rows = []
    for name, ref in DEFAULT_CATEGORIES:
        is_hidden = ref in hidden
        label = f"🚫 {name}" if is_hidden else name
        rows.append([InlineKeyboardButton(text=label, callback_data=f"cat_opt:{ref}")])
    for cat_id, name in custom:
        rows.append([InlineKeyboardButton(text=f"✏️ {name}", callback_data=f"cat_opt:c:{cat_id}")])

    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "manage_cats")
async def manage_categories(callback: CallbackQuery, db: Database):
    keyboard = await build_manage_cats_keyboard(db, callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ <b>Kategoriyalarni boshqarish</b>\n\n"
        "Kategoriyani tanlang:\n"
        "<i>🚫 — yashirilgan | ✏️ — qo'shilgan</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_opt:"))
async def category_options(callback: CallbackQuery, db: Database):
    ref = callback.data[8:]  # "d:0" yoki "c:123"

    if ref.startswith("d:"):
        idx = int(ref[2:])
        name = DEFAULT_CATEGORIES[idx][0]
        hidden = await db.get_hidden_defaults(callback.from_user.id)
        is_hidden = ref in hidden

        if is_hidden:
            toggle_text = "👁️ Ko'rsatish"
            toggle_cb = f"show_cat:{ref}"
        else:
            toggle_text = "🚫 Yashirish"
            toggle_cb = f"hide_cat:{ref}"

        await callback.message.edit_text(
            f"<b>{name}</b>\n\nNima qilmoqchisiz?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=toggle_text, callback_data=toggle_cb)],
                [InlineKeyboardButton(text="◀️ Orqaga", callback_data="manage_cats")],
            ])
        )
    else:
        cat_id = int(ref[2:])
        name = await db.get_custom_category_name(cat_id)
        if not name:
            await callback.answer("Kategoriya topilmadi.", show_alert=True)
            return

        await callback.message.edit_text(
            f"<b>{name}</b>\n\nNima qilmoqchisiz?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ O'zgartirish", callback_data=f"edit_cat:c:{cat_id}"),
                    InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"del_cat:c:{cat_id}"),
                ],
                [InlineKeyboardButton(text="◀️ Orqaga", callback_data="manage_cats")],
            ])
        )
    await callback.answer()


@router.callback_query(F.data.startswith("hide_cat:"))
async def hide_category(callback: CallbackQuery, db: Database):
    ref = callback.data[9:]
    await db.hide_default_category(callback.from_user.id, ref)
    keyboard = await build_manage_cats_keyboard(db, callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ <b>Kategoriyalarni boshqarish</b>\n\n"
        "Kategoriyani tanlang:\n"
        "<i>🚫 — yashirilgan | ✏️ — qo'shilgan</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer("🚫 Yashirildi")


@router.callback_query(F.data.startswith("show_cat:"))
async def show_category(callback: CallbackQuery, db: Database):
    ref = callback.data[9:]
    await db.show_default_category(callback.from_user.id, ref)
    keyboard = await build_manage_cats_keyboard(db, callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ <b>Kategoriyalarni boshqarish</b>\n\n"
        "Kategoriyani tanlang:\n"
        "<i>🚫 — yashirilgan | ✏️ — qo'shilgan</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer("👁️ Ko'rsatildi")


@router.callback_query(F.data.startswith("del_cat:c:"))
async def delete_category(callback: CallbackQuery, db: Database):
    cat_id = int(callback.data[10:])
    await db.delete_custom_category(cat_id, callback.from_user.id)
    keyboard = await build_manage_cats_keyboard(db, callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ <b>Kategoriyalarni boshqarish</b>\n\n"
        "Kategoriyani tanlang:\n"
        "<i>🚫 — yashirilgan | ✏️ — qo'shilgan</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer("🗑️ O'chirildi")


@router.callback_query(F.data.startswith("edit_cat:c:"))
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data[11:])
    await state.set_state(ExpenseState.waiting_edit_category_name)
    await state.update_data(edit_cat_id=cat_id)
    await callback.message.edit_text(
        "✏️ <b>Yangi nomni kiriting:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="manage_cats")]
        ])
    )
    await callback.answer()


@router.message(ExpenseState.waiting_edit_category_name)
async def handle_edit_category_name(message: Message, db: Database, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Kategoriya nomi kamida 2 ta belgi bo'lsin.")
        return
    if len(name) > 40:
        await message.answer("❌ Kategoriya nomi 40 ta belgidan oshmasin.")
        return

    data = await state.get_data()
    cat_id = data.get("edit_cat_id")
    await db.update_custom_category(cat_id, message.from_user.id, name)
    await state.clear()

    keyboard = await build_manage_cats_keyboard(db, message.from_user.id)
    await message.answer(
        f"✅ <b>Kategoriya nomi '{name}' ga o'zgartirildi!</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ── Harajatlarni boshqarish (o'chirish / o'zgartirish) ───────────────────────

@router.callback_query(F.data == "manage_exp")
async def manage_expenses(callback: CallbackQuery, db: Database):
    expenses = await db.get_recent_expenses(callback.from_user.id, limit=15)

    if not expenses:
        await callback.answer("❌ Hech qanday harajat topilmadi.", show_alert=True)
        return

    rows = []
    for exp in expenses:
        dt = datetime.fromisoformat(exp["created_at"]).strftime("%d.%m %H:%M")
        label = f"{exp['category']}  {exp['amount']:,.0f} so'm  ({dt})"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"exp:{exp['id']}")])

    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_main")])
    await callback.message.edit_text(
        "📋 <b>Harajatni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exp:"))
async def expense_options(callback: CallbackQuery, db: Database):
    expense_id = int(callback.data[4:])
    exp = await db.get_expense_by_id(expense_id, callback.from_user.id)

    if not exp:
        await callback.answer("❌ Harajat topilmadi.", show_alert=True)
        return

    dt = datetime.fromisoformat(exp["created_at"]).strftime("%d.%m.%Y %H:%M")
    await callback.message.edit_text(
        f"<b>{exp['category']}</b>\n"
        f"💵 Summa: <b>{exp['amount']:,.0f} so'm</b>\n"
        f"📅 Sana: {dt}\n\nNima qilmoqchisiz?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"del_exp:{expense_id}"),
                InlineKeyboardButton(text="✏️ O'zgartirish", callback_data=f"edit_exp:{expense_id}"),
            ],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="manage_exp")],
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_exp:"))
async def delete_expense(callback: CallbackQuery, db: Database):
    expense_id = int(callback.data[8:])
    await db.delete_expense_by_id(expense_id, callback.from_user.id)

    expenses = await db.get_recent_expenses(callback.from_user.id, limit=15)
    if not expenses:
        keyboard = await build_main_keyboard(db, callback.from_user.id)
        await callback.message.edit_text(
            "🗑️ <b>Harajat o'chirildi.</b>\n\nBoshqa harajat yo'q.",
            parse_mode="HTML", reply_markup=keyboard
        )
    else:
        rows = []
        for exp in expenses:
            dt = datetime.fromisoformat(exp["created_at"]).strftime("%d.%m %H:%M")
            label = f"{exp['category']}  {exp['amount']:,.0f} so'm  ({dt})"
            rows.append([InlineKeyboardButton(text=label, callback_data=f"exp:{exp['id']}")])
        rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_main")])
        await callback.message.edit_text(
            "🗑️ O'chirildi.\n\n📋 <b>Harajatni tanlang:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
        )
    await callback.answer("🗑️ O'chirildi")


@router.callback_query(F.data.startswith("edit_exp:"))
async def edit_expense_start(callback: CallbackQuery, state: FSMContext):
    expense_id = int(callback.data[9:])
    await state.set_state(ExpenseState.waiting_edit_amount)
    await state.update_data(edit_expense_id=expense_id)
    await callback.message.edit_text(
        "✏️ <b>Yangi summani kiriting:</b>\n<i>(masalan: 50000 yoki 50k)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_main")]
        ])
    )
    await callback.answer()


@router.message(ExpenseState.waiting_edit_amount)
async def handle_edit_amount(message: Message, db: Database, state: FSMContext):
    amount = parse_amount(message.text)

    if amount is None or amount <= 0:
        await message.answer(
            "❌ Noto'g'ri format.\n<i>Masalan: 50000 yoki 50k</i>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    expense_id = data.get("edit_expense_id")
    updated = await db.update_expense_amount(expense_id, message.from_user.id, amount)
    await state.clear()

    keyboard = await build_main_keyboard(db, message.from_user.id)
    if updated:
        await message.answer(
            f"✅ <b>Summa yangilandi!</b>\n💵 Yangi summa: <b>{amount:,.0f} so'm</b>",
            parse_mode="HTML", reply_markup=keyboard
        )
    else:
        await message.answer("❌ Yangilab bo'lmadi.", reply_markup=keyboard)


# ── Undo ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("undo:"))
async def undo_expense(callback: CallbackQuery, db: Database):
    expense_id = int(callback.data[5:])
    deleted = await db.delete_expense_by_id(expense_id, callback.from_user.id)
    if deleted:
        await callback.message.edit_text("🗑️ <b>Harajat bekor qilindi.</b>", parse_mode="HTML")
    else:
        await callback.answer("❌ Allaqachon o'chirilgan.", show_alert=True)
    await callback.answer()


# ── Har qanday matn → menyu ──────────────────────────────────────────────────

@router.message(F.text)
async def any_text(message: Message, db: Database, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

    keyboard = await build_main_keyboard(db, message.from_user.id)
    await message.answer(
        "📋 <b>Xarajat turini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_start_button()
    )
    await message.answer("Kategoriyani tanlang:", reply_markup=keyboard)
