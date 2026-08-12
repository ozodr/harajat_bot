"""
📆 Hisobot davrlari - bot va mini app uchun umumiy manba
"""
from calendar import monthrange
from datetime import date, timedelta

PERIODS = ("daily", "weekly", "monthly", "yearly")


def period_range(period: str, today: date | None = None) -> tuple[date, date, str]:
    """Davr nomidan (start, end, sarlavha) juftligini qaytaradi"""
    today = today or date.today()

    if period == "daily":
        return today, today, "Bugungi Hisobot"

    if period == "weekly":
        return today - timedelta(days=6), today, "Haftalik Hisobot (7 kun)"

    if period == "monthly":
        last_day = monthrange(today.year, today.month)[1]
        return (
            today.replace(day=1),
            today.replace(day=last_day),
            f"Oylik Hisobot ({today.strftime('%B %Y')})",
        )

    if period == "yearly":
        return (
            today.replace(month=1, day=1),
            today.replace(month=12, day=31),
            f"Yillik Hisobot ({today.year})",
        )

    raise ValueError(f"Noma'lum davr: {period}")
