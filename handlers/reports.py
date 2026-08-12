"""
📊 Hisobotlar handleri
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.database import Database
from services.periods import period_range

router = Router()
logger = logging.getLogger(__name__)


def format_report(summary: dict, title: str) -> str:
    if summary["count"] == 0:
        return f"📭 <b>{title}</b>\n\nXarajatlar topilmadi."

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
        [InlineKeyboardButton(text="◀️ Asosiy menyu", callback_data="back_main")],
    ])


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
