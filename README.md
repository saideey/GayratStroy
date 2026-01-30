# Metall Basa ERP System

Qurilish mollari do'koni uchun to'liq ERP tizimi.

## 📋 Tizim imkoniyatlari

### Asosiy modullar:

1. **👤 Foydalanuvchilar va Rollar (RBAC)**
   - Direktor, Sotuvchi, Omborchi, Buxgalter rollari
   - Ruxsatlar tizimi (permissions)
   - Login/parol autentifikatsiya

2. **📦 Mahsulotlar/Katalog**
   - Tovar kartochkalari
   - Kategoriyalar (ierarxik)
   - Ko'p o'lchov birliklari (kg, tonna, dona, m², metr)
   - Uch xil narx: kelish, sotuv, VIP
   - Rasmlar

3. **🏭 Ombor/Inventar**
   - Real vaqtda qoldiq kuzatish
   - Kirim hujjatlari (postavshchikdan)
   - Chiqim (sotuv, zarar, ichki ehtiyoj)
   - Omborlar arasi transfer
   - Inventarizatsiya

4. **💰 Sotuv/Kassa**
   - Tezkor savdo (barcode skaneri)
   - **Umumiy summa o'zgartirish** - chegirma avtomatik taqsimlanadi
   - To'lov turlari: naqd, karta, o'tkazma, qarzga, aralash
   - Chek chop etish
   - SMS yuborish (VIP uchun)

5. **👥 Mijozlar/CRM**
   - Oddiy va VIP mijozlar
   - VIP shaxsiy kabinet (login/parol)
   - Qarz va avans hisobi
   - Xarid tarixi

6. **📊 Moliya/Hisobotlar**
   - Kunlik/haftalik/oylik hisobotlar
   - Sotuvchi bo'yicha hisobot
   - Foyda hisoboti
   - Excel/PDF eksport

7. **⚙️ Sozlamalar**
   - Chegirma chegaralari
   - SMS sozlamalari
   - Telegram xabarnomalar

## 🗄️ Database Strukturasi

### O'lchov birliklari (UOM) tizimi

Har bir mahsulot uchun bir nechta o'lchov birligi:

```
Armatura 17B:
├── Base UOM: kg
├── 1 tonna = 1000 kg
├── 1 dona = 2.68 kg
└── 1 pochka = 200 kg
```

### Asosiy jadvallar:

| Modul | Jadvallar |
|-------|-----------|
| Users | roles, users, user_sessions |
| Products | categories, products, units_of_measure, product_uom_conversions |
| Warehouse | warehouses, stock, stock_movements, inventory_checks |
| Sales | sales, sale_items, payments, receipts |
| Customers | customers, customer_debts, customer_groups |
| Suppliers | suppliers, purchase_orders, supplier_payments |
| Finance | cash_registers, cash_transactions, daily_reports |
| Settings | system_settings, audit_logs, sms_logs, notifications |

## 🚀 Ishga tushirish

### Docker bilan:

```bash
# Loyihani klonlash
git clone <repo-url>
cd metall_basa

# .env faylini sozlash
cp .env.example .env
# .env ni tahrirlang

# Docker konteynerlarini ishga tushirish
docker-compose up -d

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# pgAdmin: http://localhost:5050 (ixtiyoriy)
```

### Development uchun pgAdmin bilan:

```bash
docker-compose --profile dev up -d
```

## 🔧 Muammolarni hal qilish (Troubleshooting)

### Database "password authentication failed" xatosi

Agar `password authentication failed for user "postgres"` xatosi chiqsa:

#### 1-usul: fix_db_password.sh skriptini ishlatish
```bash
chmod +x fix_db_password.sh
./fix_db_password.sh
```

#### 2-usul: Qo'lda tuzatish
```bash
# 1. PostgreSQL parolini yangilash
docker exec -it metall_basa_db psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"

# 2. API ni qayta ishga tushirish
docker restart metall_basa_api
```

#### 3-usul: Ma'lumotlarni o'chirmasdan to'liq reset
```bash
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

#### 4-usul: To'liq reset (⚠️ Ma'lumotlar o'chadi!)
```bash
docker-compose down -v
docker-compose up -d
```

### Health check
```bash
curl http://localhost:8000/health
# Javob: {"status": "healthy", "database": "connected"}
```

### Loglarni ko'rish
```bash
docker logs -f metall_basa_api
docker logs -f metall_basa_db
```

## 📁 Loyiha strukturasi

```
metall_basa/
├── docker-compose.yml
├── .env.example
├── .env
└── API/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    ├── .env
    └── database/
        ├── __init__.py
        ├── base.py
        ├── connection.py
        ├── seed.py
        └── models/
            ├── __init__.py
            ├── user.py       # Rollar, foydalanuvchilar
            ├── product.py    # Mahsulotlar, UOM
            ├── warehouse.py  # Ombor, qoldiq
            ├── sale.py       # Sotuv, to'lov
            ├── customer.py   # Mijozlar, CRM
            ├── supplier.py   # Yetkazib beruvchilar
            ├── finance.py    # Moliya, kassa
            └── settings.py   # Sozlamalar, audit
```

## 🔧 Texnologiyalar

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Container**: Docker & Docker Compose
- **Authentication**: JWT (python-jose)

## 📌 Keyingi qadamlar

1. [ ] API routerlarni qo'shish
2. [ ] Authentication middleware
3. [ ] CRUD endpointlar
4. [ ] Sotuv moduli logikasi
5. [ ] Hisobot generatorlar
6. [ ] SMS integratsiya
7. [ ] Frontend (React/Vue)

## 🤝 Muallif

Metall Basa ERP Team

---

© 2024 Metall Basa. Barcha huquqlar himoyalangan.
