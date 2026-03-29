# Telegram Bot — Yangi Funksiyalar

## Qo'shilgan imkoniyatlar

### 1. Mijoz registratsiyasi (/start)
Endi mijoz telegram_id ni qo'lda kiritish shart emas.

**Oqim:**
1. Mijoz botga `/start` yozadi
2. Bot telefon raqam so'raydi (maxsus "Telefon yuborish" tugmasi bilan)
3. Mijoz tugmani bosadi — telefoni avtomatik yuboriladi
4. Bot API orqali telefon raqamni qidiradi
5. Topilsa → Shaxsiy kabinet menyu ochiladi
6. Topilmasa → Xabar + qayta urinish imkoniyati

### 2. Shaxsiy kabinet (bot komandalar)
| Tugma | Funksiya |
|-------|---------|
| 📋 Sotuvlarim | So'nggi xaridlar (sahifalash bilan) |
| 💰 Qarzim | Qarz holati + qarz bo'lgan xaridlar + to'lovlar tarixi |
| 👤 Profilim | Shaxsiy ma'lumotlar va statistika |
| 📊 Statistika | Jami xaridlar, o'rtacha summa |
| 🌐 Shaxsiy Kabinetim | Telegram Mini App ochiladi |

### 3. Telegram Mini App (WebApp)
To'liq shaxsiy kabinet — Telegram ichida brauzer kabi ishlaydi.

**Funksiyalar:**
- 🏠 **Asosiy** — joriy qarz, jami xaridlar, statistika
- 📋 **Xaridlar** — sahifalab ko'rish, har bir xaridni bosganda tafsilot
- 💰 **Qarz** — qarz holati, harakatlar tarixi
- 👤 **Profil** — shaxsiy ma'lumotlar, moliyaviy holat

### 4. Yangi API endpointlar
`/api/v1/bot/` prefiksi ostida:

| Endpoint | Vazifa |
|----------|--------|
| `POST /bot/link-phone` | Telefon raqam → telegram_id bog'lash |
| `GET /bot/my-profile` | Mijoz profili |
| `GET /bot/my-sales` | Sotuvlar (sahifalash) |
| `GET /bot/my-sales/{id}` | Bitta sotuv tafsiloti |
| `GET /bot/my-debt` | Qarz holati va tarixi |
| `POST /bot/verify-webapp` | WebApp initData tekshirish |

---

## O'rnatish

### 1. `.env` ga qo'shing:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
DIRECTOR_TELEGRAM_IDS=123456789
WEBAPP_URL=https://yourdomain.com/webapp
COMPANY_NAME=G'ayrat Stroy House
COMPANY_PHONE=+998 99 777 55 99
```

### 2. WebApp uchun HTTPS talab qilinadi
Telegram WebApp faqat HTTPS domenida ishlaydi.

**Local test uchun ngrok:**
```bash
ngrok http 3000
# Chiqqan URL ni WEBAPP_URL ga qo'ying
```

### 3. Docker bilan ishga tushirish:
```bash
docker-compose up -d --build
```

### 4. WebApp URL ni botga belgilash:
BotFather → /mybots → Bot tanlash → Bot Settings → Menu Button → URL kiriting

---

## Fayllar tuzilmasi (yangi)

```
telegram_bot/
├── handlers/
│   ├── __init__.py
│   ├── start.py       ← /start, telefon registratsiya
│   └── menu.py        ← Shaxsiy kabinet komandalar
├── webapp/
│   └── index.html     ← Telegram Mini App
├── config.py          ← WEBAPP_URL qo'shildi
├── main.py            ← aiogram Dispatcher qo'shildi
└── ...

API/
└── routers/
    └── bot.py         ← Bot uchun yangi endpointlar
```

---

## Xavfsizlik

- `X-Telegram-Id` header orqali autentifikatsiya
- WebApp uchun `initData` Telegram imzosi tekshiriladi
- Mijoz faqat **o'z** ma'lumotlarini ko'ra oladi
- Boshqa mijoz ID si bilan so'rov yuborib bo'lmaydi (customer_id filter)
