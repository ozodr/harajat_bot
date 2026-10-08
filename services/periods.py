"""
📆 Hisobot davrlari - bot va mini app uchun umumiy manba
"""
import re
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


# ── Ixtiyoriy oraliq ─────────────────────────────────────────────────────────

CUSTOM_PERIOD = "custom"
MAX_CUSTOM_DAYS = 366 * 3

_DATE_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")


def parse_range_text(text: str) -> tuple[date, date]:
    """'10.01.2026 - 10.02.2026' kabi matndan (start, end) ni ajratadi.

    Bitta sana yozilsa — o'sha kunning o'zi. Xato bo'lsa ValueError
    (foydalanuvchiga ko'rsatiladigan matn bilan).
    """
    matches = _DATE_RE.findall(text or "")
    if not 1 <= len(matches) <= 2:
        raise ValueError("Sanani KK.OO.YYYY ko'rinishida yozing")

    dates = []
    for day, month, year in matches:
        try:
            dates.append(date(int(year), int(month), int(day)))
        except ValueError:
            raise ValueError(f"Bunday sana yo'q: {day}.{month}.{year}")

    return validate_range(dates[0], dates[-1])


def validate_range(start: date, end: date) -> tuple[date, date]:
    if start > end:
        raise ValueError("Boshlanish sanasi tugash sanasidan keyin bo'lmasin")
    if (end - start).days + 1 > MAX_CUSTOM_DAYS:
        raise ValueError("Oraliq 3 yildan oshmasin")
    return start, end


def custom_title(start: date, end: date) -> str:
    days = (end - start).days + 1
    return f"Tanlangan davr ({days} kun)"
