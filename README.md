# Finance Bot + Mini App

Telegram orqali shaxsiy xarajatlarni tez kiritish va hisobot olish uchun bot.
Bir xil ma'lumot bazasi ustida ikkita interfeys ishlaydi: **chat menyusi** va
**Telegram Mini App**.

## Imkoniyatlar

- Menyu orqali xarajat kategoriyasini tanlash
- Summa kiritish: `50000`, `50k`, `12.5k`, `60000+50000+80000`
- Maxsus kategoriyalar qo'shish, o'zgartirish va o'chirish
- Default kategoriyalarni yashirish yoki qayta ko'rsatish
- Oxirgi xarajatlarni o'chirish yoki summasini o'zgartirish
- Kunlik, haftalik, oylik va yillik hisobotlar
- Ixtiyoriy oraliq bo'yicha hisobot (masalan `10.01.2026 - 10.02.2026`)
- SQLite bazada ma'lumot saqlash

## Mini App

Mini App botning barcha vazifalarini takrorlaydi — modullar bot bo'limlariga
mos keladi:

| Mini App bo'limi | Botdagi muqobili |
|---|---|
| 🏠 **Asosiy** — bugun/hafta/oy jamlanmasi va xarajat tarixi (bosib o'zgartirish yoki o'chirish) | «✏️ Harajatni o'chirish/o'zgartirish» |
| ➕ **Qo'shish** — kategoriya tanlash + raqamli klaviatura (`➕ Yana qo'shish` bilan summalarni qo'shish) | Kategoriya tugmasi → summa yuborish |
| 📊 **Hisobot** — Bugun / Hafta / Oy / Yil / Oraliq, kunlar (yoki oylar) kesimidagi grafik va kategoriya ustunlari | «📊 Bugungi», «📅 Haftalik», «🗓️ Oylik», «📆 Yillik», «📅 Oraliq tanlash» |
| ⚙️ **Kategoriya** — qo'shish, nomini o'zgartirish, o'chirish, yashirish/ko'rsatish | «➕ Kategoriya qo'shish», «⚙️ Boshqarish» |

Dizayn Telegram mavzusiga moslashadi (light/dark), tugmalar haptik javob beradi.

Mini App'ni ochish uchun uchta yo'l bor: chat menyusidagi **Mini App** tugmasi,
klaviaturadagi **📱 Mini App** tugmasi va `/app` buyrug'i.

### Xavfsizlik

Har bir API so'rovi `X-Init-Data` sarlavhasidagi Telegram `initData` bilan
tekshiriladi (HMAC-SHA256, bot tokeni asosida). Imzo noto'g'ri yoki 24 soatdan
eski bo'lsa so'rov rad etiladi. Har bir yozuv faqat o'z egasiga ko'rinadi.

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

3. `.env` ichiga sozlamalarni yozing:

```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_PATH=finance.db
WEBAPP_URL=https://sizning-manzilingiz.up.railway.app
PORT=8080
```

`WEBAPP_URL` bo'sh qolsa bot Mini App tugmalarisiz, faqat menyu rejimida
ishlayveradi. Telegram faqat **HTTPS** manzilni qabul qiladi.
Railway'da bu qiymatni qo'lda yozish shart emas — domen avtomatik aniqlanadi
(pastdagi «Deploy» bo'limiga qarang).

4. Botni ishga tushiring:

```bash
python bot.py
```

Bitta jarayonda ikkalasi ham ishlaydi: bot polling va `PORT` dagi Mini App serveri.

## Telegram bot token olish

Telegramda [@BotFather](https://t.me/BotFather) orqali yangi bot yarating va tokenni `.env` fayliga yozing.

## Lokalda Mini App'ni sinash

Telegram lokal `http://localhost` manzilini ocholmaydi, shuning uchun tunnel kerak:

```bash
python bot.py           # 8080-portda server ko'tariladi
ngrok http 8080         # boshqa terminalda
```

`ngrok` bergan `https://...` manzilni `.env` dagi `WEBAPP_URL` ga yozing va
botni qayta ishga tushiring.

## Loyiha tuzilmasi

```text
finance_bot/
├── bot.py                 # Bot polling + Mini App serverini ishga tushirish
├── config.py              # Muhit sozlamalari
├── requirements.txt       # Python kutubxonalari
├── railway.json           # Railway deploy sozlamasi
├── .python-version        # Railway uchun Python versiyasi
├── handlers/
│   ├── expenses.py        # Xarajat va kategoriya handlerlari
│   └── reports.py         # Hisobot handlerlari
├── services/
│   ├── database.py        # SQLite amallari
│   ├── categories.py      # Kategoriyalar (bot va Mini App uchun umumiy)
│   └── periods.py         # Hisobot davrlari (umumiy)
└── webapp/
    ├── server.py          # aiohttp server va JSON API
    ├── auth.py            # initData imzosini tekshirish
    └── static/            # Mini App: index.html, app.js, styles.css
```

## API (Mini App uchun)

Barcha `/api/...` so'rovlari `X-Init-Data` sarlavhasini talab qiladi.

| Metod | Manzil | Vazifa |
|---|---|---|
| GET | `/api/me` | Foydalanuvchi profili |
| GET | `/api/overview` | Bugun/hafta/oy jamlanmasi + so'nggi 5 yozuv |
| GET | `/api/categories` | Kategoriyalar ro'yxati |
| POST | `/api/categories` | Kategoriya qo'shish |
| PATCH | `/api/categories/{id}` | Nomini o'zgartirish |
| DELETE | `/api/categories/{id}` | O'chirish |
| POST | `/api/categories/visibility` | Standart kategoriyani yashirish/ko'rsatish |
| GET | `/api/expenses?limit=` | So'nggi xarajatlar |
| POST | `/api/expenses` | Xarajat qo'shish |
| PATCH | `/api/expenses/{id}` | Summani o'zgartirish |
| DELETE | `/api/expenses/{id}` | O'chirish |
| GET | `/api/report?period=` | `daily` / `weekly` / `monthly` / `yearly` |

## Deploy — Railway

Sozlama [railway.json](railway.json) da: builder `RAILPACK`, start komandasi
`python bot.py`, holat tekshiruvi `/healthz`, xatolikda avtomatik qayta ishga
tushish.

### 1. Loyihani yarating

Dashboard orqali: **New Project → Deploy from GitHub repo** va shu reponi tanlang.

Yoki CLI orqali:

```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### 2. Domen oching

Service → **Settings → Networking → Generate Domain**.

Bu qadam muhim: domen yaratilgach Railway `RAILWAY_PUBLIC_DOMAIN` o'zgaruvchisini
beradi va bot Mini App manzilini o'zi shundan yasaydi — `WEBAPP_URL` ni qo'lda
yozish shart emas. Domen yaratilgandan keyin servisni bir marta qayta ishga
tushiring (**Redeploy**).

### 3. Volume ulang (baza yo'qolmasligi uchun)

Service → **Variables/Settings → + Volume**. Mount path sifatida `/data` bering.

Railway `RAILWAY_VOLUME_MOUNT_PATH` ni beradi va baza avtomatik ravishda
`/data/finance.db` da saqlanadi. Volumesiz har deployda ma'lumot yo'qoladi.

### 4. O'zgaruvchilar

| O'zgaruvchi | Qiymat |
|---|---|
| `BOT_TOKEN` | @BotFather bergan token — **majburiy** |
| `WEBAPP_URL` | Kerak emas (domendan avtomatik). Faqat maxsus domen ishlatsangiz yozing |
| `DATABASE_PATH` | Kerak emas (volume'dan avtomatik) |
| `PORT` | **O'rnatmang** — Railway o'zi beradi |

### Eslatmalar

- Volume ulangan servisda replikalar ishlamaydi (`numReplicas: 1`), va har
  deployda qisqa uzilish bo'ladi — bu SQLite uchun to'g'ri xatti-harakat.
- Bot polling rejimida ishlagani uchun servis doim uyg'oq turishi kerak;
  «serverless / sleep» rejimini yoqmang.
- Bitta jarayonda ikkalasi ishlaydi, shuning uchun alohida worker kerak emas.

## Eslatma

AI va ovozli xabar qismlari loyihadan olib tashlangan. Hozirgi versiya oddiy,
tez va barqaror xarajat kuzatuvchi bot hamda unga mos Mini App'dan iborat.
