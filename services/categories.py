"""
🏷️ Kategoriyalar - bot va mini app uchun umumiy manba
"""
from services.database import Database

DEFAULT_CATEGORIES = [
    ("🍽️ Ovqatlanish", "d:0"),
    ("🎮 Kompyuter oyinlari", "d:1"),
    ("👔 Kiyinish", "d:2"),
    ("🚗 Yo'l haqqi", "d:3"),
    ("💸 Qarz berish", "d:4"),
    ("🏠 Uy-ro'zg'or", "d:5"),
]

CATEGORY_NAME_MIN = 2
CATEGORY_NAME_MAX = 40


async def resolve_category(db: Database, user_id: int, ref: str) -> str | None:
    """'d:0' yoki 'c:12' ko'rinishidagi ref'dan kategoriya nomini olish"""
    if ref.startswith("d:"):
        try:
            idx = int(ref[2:])
        except ValueError:
            return None
        if 0 <= idx < len(DEFAULT_CATEGORIES):
            return DEFAULT_CATEGORIES[idx][0]
        return None

    if ref.startswith("c:"):
        try:
            cat_id = int(ref[2:])
        except ValueError:
            return None
        return await db.get_custom_category_name(cat_id)

    return None


async def list_categories(db: Database, user_id: int) -> list[dict]:
    """Foydalanuvchi uchun barcha kategoriyalar (yashirilganlik belgisi bilan)"""
    hidden = await db.get_hidden_defaults(user_id)
    custom = await db.get_custom_categories(user_id)

    items = [
        {"ref": ref, "name": name, "custom": False, "hidden": ref in hidden}
        for name, ref in DEFAULT_CATEGORIES
    ]
    items += [
        {"ref": f"c:{cat_id}", "name": name, "custom": True, "hidden": False}
        for cat_id, name in custom
    ]
    return items
