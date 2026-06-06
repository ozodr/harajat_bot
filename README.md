# 💰 Moliyaviy Harajat Telegram Boti

AI yordamida shaxsiy moliyaviy harajatlarni kuzatuvchi Telegram bot.

## 🌟 Imkoniyatlar

- 📝 **Matnli kiritish** — harajatni oddiy so'zlarda yozing
- 🎤 **Ovozli kiritish** — ovozli xabar yuboring, AI matnga aylantiradi
- 🤖 **AI kategoriyalash** — Claude AI avtomatik tur belgilaydi
- 📊 **Hisobotlar** — kunlik, haftalik, oylik, yillik statistika
- 🗑️ **O'chirish** — oxirgi yozuvni bekor qilish

## 🚀 O'rnatish

### 1. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 2. API kalitlarni sozlash
`.env.example` faylini `.env` nomi bilan nusxalang:
```bash
cp .env.example .env
```

`.env` faylini tahrirlang:
```
BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key  # ixtiyoriy
```

### 3. API kalitlarni olish
| Xizmat | Havola | Maqsad |
|--------|--------|--------|
| Telegram Bot | [@BotFather](https://t.me/BotFather) | Bot yaratish |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | Matn tahlili |
| OpenAI | [platform.openai.com](https://platform.openai.com) | Ovozni matnga (ixtiyoriy) |

### 4. Botni ishga tushirish
```bash
python bot.py
```

## 📁 Loyiha tuzilmasi

```
finance_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Sozlamalar
├── requirements.txt    # Kutubxonalar
├── .env               # API kalitlar (gitga qo'shmang!)
├── handlers/
│   ├── expenses.py    # Harajat qo'shish
│   ├── reports.py     # Hisobotlar
│   └── voice.py       # Ovozli xabar
└── services/
    ├── database.py    # SQLite baza
    └── ai_service.py  # Claude AI
```

## 💡 Foydalanish misollari

```
Non uchun 5000 so'm sarfladim
Taksi 15000
Kino 80k
Aptekada dori 45000
```

Yoki ovozli xabar yuboring!

## 🏷️ Kategoriyalar

Bot quyidagi kategoriyalarni avtomatik aniqlaydi:
- 🍔 Oziq-ovqat
- 🚗 Transport  
- 🏠 Uy-joy
- 👕 Kiyim
- 💊 Salomatlik
- 🎓 Ta'lim
- 🎮 Ko'ngil ochar
- 📱 Texnologiya
- 🍽️ Restoran/Kafe
- va boshqalar...
