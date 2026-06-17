# Finance Bot

Telegram orqali shaxsiy xarajatlarni tez kiritish va hisobot olish uchun kichik bot.

## Imkoniyatlar

- Menyu orqali xarajat kategoriyasini tanlash
- Summa kiritish: `50000`, `50k`, `12.5k`, `60000+50000+80000`
- Maxsus kategoriyalar qo'shish, o'zgartirish va o'chirish
- Default kategoriyalarni yashirish yoki qayta ko'rsatish
- Oxirgi xarajatlarni o'chirish yoki summasini o'zgartirish
- Kunlik, haftalik, oylik va yillik hisobotlar
- SQLite bazada ma'lumot saqlash

## O'rnatish

1. Kutubxonalarni o'rnating:

```bash
pip install -r requirements.txt
```

2. `.env.example` faylidan `.env` yarating:

```bash
cp .env.example .env
```

Windows PowerShell uchun:

```powershell
Copy-Item .env.example .env
```

3. `.env` ichiga Telegram bot tokenini yozing:

```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_PATH=finance.db
```

4. Botni ishga tushiring:

```bash
python bot.py
```

## Telegram bot token olish

Telegramda [@BotFather](https://t.me/BotFather) orqali yangi bot yarating va tokenni `.env` fayliga yozing.

## Loyiha tuzilmasi

```text
finance_bot/
├── bot.py                 # Botni ishga tushirish
├── config.py              # Muhit sozlamalari
├── requirements.txt       # Python kutubxonalari
├── render.yaml            # Render worker sozlamasi
├── handlers/
│   ├── expenses.py        # Xarajat va kategoriya handlerlari
│   └── reports.py         # Hisobot handlerlari
└── services/
    └── database.py        # SQLite amallari
```

## Deploy

`render.yaml` Render worker sifatida sozlangan. Render dashboardida `BOT_TOKEN` environment variable sifatida kiritiladi. Bazani saqlash uchun `/var/data/finance.db` disk path ishlatiladi.

## Eslatma

AI va ovozli xabar qismlari loyihadan olib tashlangan. Hozirgi versiya oddiy, tez va barqaror menyu-asosli xarajat kuzatuvchi bot sifatida ishlaydi.
