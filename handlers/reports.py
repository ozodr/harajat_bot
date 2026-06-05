"""
📊 Hisobotlar handleri
"""
import logging
from datetime import date, timedelta
from calendar import monthrange
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.database import Database

router = Router()
logger = logging.getLogger(__name__)


def format_report(summary: dict, title: str) -> str:
    if summary["count"] == 0:
        return f"📭 <b>{title}</b>\n\nHarajatlar topilmadi."

    lines = [
        f"📊 <b>{title}</b>",
        f"📅 {summary['start_date'].strftime('%d.%m.%Y')} — {summary['end_date'].strftime('%d.%m.%Y')}",
        f"",
        f"💵 <b>Jami: {summary['total']:,.0f} so'm</b>",
        f"📝 Yozuvlar soni: {summary['count']} ta",
        f"",
        f"📂 <b>Kategoriyalar bo'yicha:</b>",
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


@router.callback_query(F.data == "report_daily")
async def report_daily(callback: CallbackQuery, db: Database):
    today = date.today()
    summary = await db.get_summary(callback.from_user.id, today, today)
    text = format_report(summary, "Bugungi Hisobot")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_report_keyboard())
    await callback.answer()


@router.callback_query(F.data == "report_weekly")
async def report_weekly(callback: CallbackQuery, db: Database):
    end = date.today()
    start = end - timedelta(days=6)
    summary = await db.get_summary(callback.from_user.id, start, end)
    text = format_report(summary, "Haftalik Hisobot (7 kun)")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_report_keyboard())
    await callback.answer()


@router.callback_query(F.data == "report_monthly")
async def report_monthly(callback: CallbackQuery, db: Database):
    today = date.today()
    start = today.replace(day=1)
    last_day = monthrange(today.year, today.month)[1]
    end = today.replace(day=last_day)
    summary = await db.get_summary(callback.from_user.id, start, end)
    month_name = today.strftime("%B %Y")
    text = format_report(summary, f"Oylik Hisobot ({month_name})")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_report_keyboard())
    await callback.answer()


@router.callback_query(F.data == "report_yearly")
async def report_yearly(callback: CallbackQuery, db: Database):
    today = date.today()
    start = today.replace(month=1, day=1)
    end = today.replace(month=12, day=31)
    summary = await db.get_summary(callback.from_user.id, start, end)
    text = format_report(summary, f"Yillik Hisobot ({today.year})")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_report_keyboard())
    await callback.answer()
