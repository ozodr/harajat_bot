"""
📊 Hisobotlar handleri
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.database import Database
from services.periods import custom_title, parse_range_text, period_range

router = Router()
logger = logging.getLogger(__name__)

RANGE_PROMPT_TEXT = (
    "📅 <b>Oraliqni tanlang</b>\n\n"
    "Boshlanish va tugash sanasini yuboring:\n"
    "<code>10.01.2026 - 10.02.2026</code>\n\n"
    "<i>Bitta sana yuborsangiz — o'sha kun hisoboti.</i>"
)


class ReportState(StatesGroup):
    waiting_range = State()


def format_report(summary: dict, title: str) -> str:
    if summary["count"] == 0:
        return (
            f"📭 <b>{title}</b>\n"
            f"📅 {summary['start_date'].strftime('%d.%m.%Y')} — {summary['end_date'].strftime('%d.%m.%Y')}\n\n"
            "Xarajatlar topilmadi."
        )

    lines = [
        f"📊 <b>{title}</b>",
        f"📅 {summary['start_date'].strftime('%d.%m.%Y')} — {summary['end_date'].strftime('%d.%m.%Y')}",
        "",
        f"💵 <b>Jami: {summary['total']:,.0f} so'm</b>",
        f"📝 Yozuvlar soni: {summary['count']} ta",
        "",
        "📂 <b>Kategoriyalar bo'yicha:</b>",
    ]

    total = summary["total"]
    for cat in summary["categories"]:
        percent = (cat["total"] / total * 100) if total > 0 else 0
        bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
        lines.append(
            f"\n{cat['category']}\n"
            f"  {bar} {percent:.0f}%\n"
            f"  💰 {cat['total']:,.0f} so'm ({cat['count']} ta)"
        )

    return "\n".join(lines)


def get_report_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Bugungi", callback_data="report_daily"),
            InlineKeyboardButton(text="📅 Haftalik", callback_data="report_weekly"),
        ],
        [
            InlineKeyboardButton(text="🗓️ Oylik", callback_data="report_monthly"),
            InlineKeyboardButton(text="📆 Yillik", callback_data="report_yearly"),
        ],
        [InlineKeyboardButton(text="📅 Oraliq tanlash", callback_data="report_custom")],
        [InlineKeyboardButton(text="◀️ Asosiy menyu", callback_data="back_main")],
    ])


# ── Ixtiyoriy oraliq ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "report_custom")
async def ask_custom_range(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReportState.waiting_range)
    await callback.message.edit_text(
        RANGE_PROMPT_TEXT,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_main")]
        ])
    )
    await callback.answer()


@router.message(ReportState.waiting_range)
async def handle_custom_range(message: Message, db: Database, state: FSMContext):
    try:
        start, end = parse_range_text(message.text or "")
    except ValueError as err:
        await message.answer(
            f"❌ {err}\n<i>Masalan: 10.01.2026 - 10.02.2026</i>",
            parse_mode="HTML"
        )
        return

    await state.clear()
    summary = await db.get_summary(message.from_user.id, start, end)
    text = format_report(summary, custom_title(start, end))
    await message.answer(text, parse_mode="HTML", reply_markup=get_report_keyboard())


# ── Tayyor davrlar ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("report_"))
async def show_report(callback: CallbackQuery, db: Database):
    period = callback.data[len("report_"):]

    try:
        start, end, title = period_range(period)
    except ValueError:
        await callback.answer("Noma'lum hisobot turi.", show_alert=True)
        return

    summary = await db.get_summary(callback.from_user.id, start, end)
    text = format_report(summary, title)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_report_keyboard())
    await callback.answer()
