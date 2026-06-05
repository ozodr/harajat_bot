"""
🗄️ Database xizmati - SQLite bilan ishlash
"""
import aiosqlite
import logging
from datetime import date
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH

    async def init(self):
        """Jadvallarni yaratish"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS custom_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS hidden_categories (
                    user_id INTEGER NOT NULL,
                    category_ref TEXT NOT NULL,
                    PRIMARY KEY (user_id, category_ref)
                )
            """)
            await db.commit()
        logger.info("✅ Database tayyor")

    async def add_expense(self, user_id: int, amount: float, category: str, description: str = "") -> int:
        """Yangi harajat qo'shish"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO expenses (user_id, amount, category, description) VALUES (?, ?, ?, ?)",
                (user_id, amount, category, description)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_custom_categories(self, user_id: int) -> list[tuple[int, str]]:
        """Foydalanuvchining maxsus kategoriyalari (id, name)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, name FROM custom_categories WHERE user_id = ? ORDER BY created_at",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [(row[0], row[1]) for row in rows]

    async def get_custom_category_name(self, cat_id: int) -> str | None:
        """ID bo'yicha kategoriya nomini olish"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM custom_categories WHERE id = ?",
                (cat_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def add_custom_category(self, user_id: int, name: str) -> bool:
        """Yangi kategoriya qo'shish"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO custom_categories (user_id, name) VALUES (?, ?)",
                    (user_id, name)
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Kategoriya qo'shishda xato: {e}")
            return False

    async def get_expenses(self, user_id: int, start_date: date, end_date: date) -> list:
        """Ma'lum vaqt oralig'idagi harajatlar"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM expenses
                WHERE user_id = ?
                AND DATE(created_at) BETWEEN ? AND ?
                ORDER BY created_at DESC
            """, (user_id, start_date.isoformat(), end_date.isoformat()))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_summary(self, user_id: int, start_date: date, end_date: date) -> dict:
        """Kategoriya bo'yicha umumiy xulosa"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total,
                       COUNT(*) as count
                FROM expenses
                WHERE user_id = ?
                AND DATE(created_at) BETWEEN ? AND ?
            """, (user_id, start_date.isoformat(), end_date.isoformat()))
            totals = dict(await cursor.fetchone())

            cursor = await db.execute("""
                SELECT category,
                       SUM(amount) as total,
                       COUNT(*) as count
                FROM expenses
                WHERE user_id = ?
                AND DATE(created_at) BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
            """, (user_id, start_date.isoformat(), end_date.isoformat()))
            rows = await cursor.fetchall()
            categories = [dict(row) for row in rows]

        return {
            "total": totals["total"],
            "count": totals["count"],
            "categories": categories,
            "start_date": start_date,
            "end_date": end_date
        }

    async def get_hidden_defaults(self, user_id: int) -> set:
        """Yashirilgan default kategoriyalar ro'yxati"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT category_ref FROM hidden_categories WHERE user_id = ?", (user_id,)
            )
            rows = await cursor.fetchall()
            return {row[0] for row in rows}

    async def hide_default_category(self, user_id: int, ref: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO hidden_categories (user_id, category_ref) VALUES (?, ?)",
                (user_id, ref)
            )
            await db.commit()

    async def show_default_category(self, user_id: int, ref: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM hidden_categories WHERE user_id = ? AND category_ref = ?",
                (user_id, ref)
            )
            await db.commit()

    async def update_custom_category(self, cat_id: int, user_id: int, new_name: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE custom_categories SET name = ? WHERE id = ? AND user_id = ?",
                (new_name, cat_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_custom_category(self, cat_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM custom_categories WHERE id = ? AND user_id = ?",
                (cat_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_recent_expenses(self, user_id: int, limit: int = 15) -> list:
        """So'nggi harajatlar ro'yxati"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT id, amount, category, created_at
                FROM expenses
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_expense_by_id(self, expense_id: int, user_id: int) -> dict | None:
        """ID bo'yicha bitta harajat"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, amount, category, created_at FROM expenses WHERE id = ? AND user_id = ?",
                (expense_id, user_id)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_expense_amount(self, expense_id: int, user_id: int, new_amount: float) -> bool:
        """Harajat summasini yangilash"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE expenses SET amount = ? WHERE id = ? AND user_id = ?",
                (new_amount, expense_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_expense_by_id(self, expense_id: int, user_id: int) -> bool:
        """ID bo'yicha harajatni o'chirish (faqat o'z harajatini)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                (expense_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_last_expense(self, user_id: int) -> bool:
        """Oxirgi harajatni o'chirish"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id FROM expenses
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            row = await cursor.fetchone()
            if not row:
                return False
            await db.execute("DELETE FROM expenses WHERE id = ?", (row[0],))
            await db.commit()
            return True
