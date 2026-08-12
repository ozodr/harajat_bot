"""
💰 Finance Tracker Bot - Asosiy fayl

Bitta jarayonda ikkita xizmat ishlaydi:
  • Telegram bot (aiogram polling)
  • Mini App uchun HTTP server (aiohttp)
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from config import BOT_TOKEN, PORT, WEBAPP_URL
from handlers import expenses, reports
from services.database import Database
from webapp.server import start_webapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def setup_menu_button(bot: Bot):
    """Chat menyusidagi tugmani Mini App'ga bog'laydi"""
    if WEBAPP_URL:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
        )
        logger.info(f"📱 Mini App tugmasi ulandi: {WEBAPP_URL}")
    else:
        logger.warning("⚠️ WEBAPP_URL o'rnatilmagan — Mini App tugmalari ko'rsatilmaydi")


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
        BotCommand(command="app", description="Mini App'ni ochish"),
    ])
    await setup_menu_button(bot)

    runner = await start_webapp(db, PORT)
    logger.info("🤖 Bot ishga tushmoqda...")

    try:
        await dp.start_polling(bot, db=db)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
