"""
🌐 Mini App uchun HTTP server (aiohttp)

Statik fayllar `/` manzilida, JSON API esa `/api/...` da beriladi.
Har bir API so'rovi `X-Init-Data` sarlavhasidagi Telegram initData bilan
autentifikatsiya qilinadi.
"""
import logging
from datetime import date, datetime
from pathlib import Path

from aiohttp import web

from config import BOT_TOKEN
from services.categories import (
    CATEGORY_NAME_MAX,
    CATEGORY_NAME_MIN,
    list_categories,
    resolve_category,
)
from services.database import Database
from services.periods import CUSTOM_PERIOD, PERIODS, custom_title, period_range, validate_range
from webapp.auth import validate_init_data

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
MAX_AMOUNT = 1_000_000_000


class ApiError(Exception):
    """Foydalanuvchiga ko'rsatiladigan xato (JSON javob sifatida qaytariladi)"""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


@web.middleware
async def api_middleware(request: web.Request, handler):
    """API so'rovlarini initData orqali tekshiradi va xatolarni JSON qiladi"""
    if not request.path.startswith("/api/"):
        return await handler(request)

    user = validate_init_data(request.headers.get("X-Init-Data", ""), BOT_TOKEN)
    if not user:
        return web.json_response({"error": "Avtorizatsiya amalga oshmadi"}, status=401)

    request["user_id"] = user["id"]
    request["user"] = user

    try:
        return await handler(request)
    except ApiError as err:
        return web.json_response({"error": err.message}, status=err.status)
    except Exception:
        logger.exception("API xatosi: %s %s", request.method, request.path)
        return web.json_response({"error": "Serverda xatolik"}, status=500)


async def read_json(request: web.Request) -> dict:
    try:
        body = await request.json()
    except Exception:
        raise ApiError("Ma'lumot formati noto'g'ri")
    if not isinstance(body, dict):
        raise ApiError("Ma'lumot formati noto'g'ri")
    return body


def parse_amount_value(raw) -> float:
    """Summani tekshirib float qaytaradi"""
    try:
        amount = float(raw)
    except (TypeError, ValueError):
        raise ApiError("Noto'g'ri summa")
    if not (0 < amount <= MAX_AMOUNT):
        raise ApiError("Summa 0 dan katta bo'lishi kerak")
    return round(amount, 2)


def clean_category_name(raw) -> str:
    name = raw.strip() if isinstance(raw, str) else ""
    if not (CATEGORY_NAME_MIN <= len(name) <= CATEGORY_NAME_MAX):
        raise ApiError(f"Nom {CATEGORY_NAME_MIN}-{CATEGORY_NAME_MAX} ta belgi bo'lsin")
    return name


def serialize_expense(exp: dict) -> dict:
    return {
        "id": exp["id"],
        "amount": exp["amount"],
        "category": exp["category"],
        "created_at": exp["created_at"],
    }


# ── Profil ───────────────────────────────────────────────────────────────────

async def api_me(request: web.Request) -> web.Response:
    user = request["user"]
    return web.json_response({
        "id": user["id"],
        "first_name": user.get("first_name", ""),
        "username": user.get("username", ""),
        "photo_url": user.get("photo_url", ""),
    })


# ── Kategoriyalar ─────────────────────────────────────────────────────────────

async def api_categories(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    items = await list_categories(db, request["user_id"])
    return web.json_response({"categories": items})


async def api_add_category(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    body = await read_json(request)
    name = clean_category_name(body.get("name"))
    await db.add_custom_category(request["user_id"], name)
    items = await list_categories(db, request["user_id"])
    return web.json_response({"categories": items})


async def api_update_category(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    body = await read_json(request)
    name = clean_category_name(body.get("name"))
    cat_id = int(request.match_info["cat_id"])

    updated = await db.update_custom_category(cat_id, request["user_id"], name)
    if not updated:
        raise ApiError("Kategoriya topilmadi", 404)

    items = await list_categories(db, request["user_id"])
    return web.json_response({"categories": items})


async def api_delete_category(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    cat_id = int(request.match_info["cat_id"])

    deleted = await db.delete_custom_category(cat_id, request["user_id"])
    if not deleted:
        raise ApiError("Kategoriya topilmadi", 404)

    items = await list_categories(db, request["user_id"])
    return web.json_response({"categories": items})


async def api_toggle_category(request: web.Request) -> web.Response:
    """Default kategoriyani yashirish / ko'rsatish"""
    db: Database = request.app["db"]
    body = await read_json(request)
    ref = body.get("ref", "")
    user_id = request["user_id"]

    if not isinstance(ref, str) or not ref.startswith("d:"):
        raise ApiError("Faqat standart kategoriyani yashirish mumkin")
    if await resolve_category(db, user_id, ref) is None:
        raise ApiError("Kategoriya topilmadi", 404)

    if body.get("hidden"):
        await db.hide_default_category(user_id, ref)
    else:
        await db.show_default_category(user_id, ref)

    items = await list_categories(db, user_id)
    return web.json_response({"categories": items})


# ── Xarajatlar ────────────────────────────────────────────────────────────────

async def api_expenses(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    try:
        limit = min(max(int(request.query.get("limit", 30)), 1), 100)
    except ValueError:
        limit = 30

    rows = await db.get_recent_expenses(request["user_id"], limit=limit)
    return web.json_response({"expenses": [serialize_expense(e) for e in rows]})


async def api_add_expense(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    body = await read_json(request)
    user_id = request["user_id"]

    amount = parse_amount_value(body.get("amount"))
    ref = body.get("ref", "")
    category = await resolve_category(db, user_id, ref) if isinstance(ref, str) else None
    if not category:
        raise ApiError("Kategoriya topilmadi", 404)

    expense_id = await db.add_expense(user_id=user_id, amount=amount, category=category)
    return web.json_response({
        "expense": {
            "id": expense_id,
            "amount": amount,
            "category": category,
            "created_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        }
    })


async def api_update_expense(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    body = await read_json(request)
    amount = parse_amount_value(body.get("amount"))
    expense_id = int(request.match_info["expense_id"])

    updated = await db.update_expense_amount(expense_id, request["user_id"], amount)
    if not updated:
        raise ApiError("Xarajat topilmadi", 404)

    return web.json_response({"ok": True, "amount": amount})


async def api_delete_expense(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    expense_id = int(request.match_info["expense_id"])

    deleted = await db.delete_expense_by_id(expense_id, request["user_id"])
    if not deleted:
        raise ApiError("Xarajat topilmadi", 404)

    return web.json_response({"ok": True})


# ── Hisobotlar ────────────────────────────────────────────────────────────────

async def api_report(request: web.Request) -> web.Response:
    db: Database = request.app["db"]
    user_id = request["user_id"]

    period = request.query.get("period", "daily")
    today = date.today()

    if period == CUSTOM_PERIOD:
        try:
            start = date.fromisoformat(request.query.get("start", ""))
            end = date.fromisoformat(request.query.get("end", ""))
        except ValueError:
            raise ApiError("Sanalar noto'g'ri")
        try:
            start, end = validate_range(start, end)
        except ValueError as err:
            raise ApiError(str(err))
        title = custom_title(start, end)
    elif period in PERIODS:
        start, end, title = period_range(period, today)
    else:
        raise ApiError("Noma'lum davr")

    summary = await db.get_summary(user_id, start, end)
    trend = await db.get_daily_totals(user_id, start, end) if start != end else []

    return web.json_response({
        "period": period,
        "title": title,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "today": today.isoformat(),
        "total": summary["total"],
        "count": summary["count"],
        "categories": summary["categories"],
        "trend": trend,
    })


async def api_overview(request: web.Request) -> web.Response:
    """Asosiy ekran uchun bugun / hafta / oy jamlanmasi"""
    db: Database = request.app["db"]
    user_id = request["user_id"]

    result = {}
    for period in ("daily", "weekly", "monthly"):
        start, end, _ = period_range(period)
        summary = await db.get_summary(user_id, start, end)
        result[period] = {"total": summary["total"], "count": summary["count"]}

    recent = await db.get_recent_expenses(user_id, limit=5)
    result["recent"] = [serialize_expense(e) for e in recent]
    return web.json_response(result)


# ── App ───────────────────────────────────────────────────────────────────────

async def index(request: web.Request) -> web.Response:
    return web.FileResponse(STATIC_DIR / "index.html")


async def healthz(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app(db: Database) -> web.Application:
    app = web.Application(middlewares=[api_middleware])
    app["db"] = db

    app.add_routes([
        web.get("/", index),
        web.get("/healthz", healthz),

        web.get("/api/me", api_me),
        web.get("/api/overview", api_overview),

        web.get("/api/categories", api_categories),
        web.post("/api/categories", api_add_category),
        web.patch("/api/categories/{cat_id:\\d+}", api_update_category),
        web.delete("/api/categories/{cat_id:\\d+}", api_delete_category),
        web.post("/api/categories/visibility", api_toggle_category),

        web.get("/api/expenses", api_expenses),
        web.post("/api/expenses", api_add_expense),
        web.patch("/api/expenses/{expense_id:\\d+}", api_update_expense),
        web.delete("/api/expenses/{expense_id:\\d+}", api_delete_expense),

        web.get("/api/report", api_report),
    ])
    app.router.add_static("/static/", STATIC_DIR, name="static")
    return app


async def start_webapp(db: Database, port: int) -> web.AppRunner:
    """Serverni fon rejimida ishga tushiradi"""
    runner = web.AppRunner(create_app(db))
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info(f"🌐 Mini App server {port}-portda ishlamoqda")
    return runner
