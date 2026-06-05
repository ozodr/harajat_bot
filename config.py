"""
⚙️ Konfiguratsiya fayli
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8638120837:AAFZbffpFxLtpM1BmEspgvjcoR3suc4sbN8")
DATABASE_PATH = "finance.db"
