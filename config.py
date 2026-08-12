"""
⚙️ Konfiguratsiya fayli

Railway'da ishlaganda ko'p narsa avtomatik aniqlanadi:
  • PORT                      — Railway o'zi kiritadi
  • RAILWAY_PUBLIC_DOMAIN     — Mini App manzili shundan yasaladi
  • RAILWAY_VOLUME_MOUNT_PATH — baza shu diskda saqlanadi
Kerak bo'lsa har birini qo'lda o'rnatib, ustidan yozish mumkin.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")

# ── Baza ─────────────────────────────────────────────────────────────────────
# Volume ulangan bo'lsa baza o'sha yerda saqlanadi, aks holda joriy papkada.
_volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip().rstrip("/")
_default_db = f"{_volume_path}/finance.db" if _volume_path else "finance.db"
DATABASE_PATH = os.getenv("DATABASE_PATH", "").strip() or _default_db

# ── Mini App ─────────────────────────────────────────────────────────────────
# WEBAPP_URL bo'sh bo'lsa Railway bergan domendan yasaladi.
# Ikkalasi ham bo'lmasa bot Mini App tugmalarisiz, faqat menyu rejimida ishlaydi.
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
if not WEBAPP_URL:
    _railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if _railway_domain:
        WEBAPP_URL = f"https://{_railway_domain}"

if WEBAPP_URL and not WEBAPP_URL.startswith("https://"):
    raise ValueError("WEBAPP_URL https:// bilan boshlanishi shart (Telegram talabi)!")

# Railway ishga tushirishda PORT ni o'zi beradi.
PORT = int(os.getenv("PORT", "8080"))
