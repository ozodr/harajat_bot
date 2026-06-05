"""
💰 Finance Tracker Bot - Asosiy fayl
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from handlers import expenses, reports
from services.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    db = Database()
    await db.init()

    dp.include_router(expenses.router)
    dp.include_router(reports.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="menu", description="Menyuni ko'rish"),
    ])

    logger.info("🤖 Bot ishga tushmoqda...")

    try:
        await dp.start_polling(bot, db=db)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
