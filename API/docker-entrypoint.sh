#!/bin/bash
set -e

echo "🔄 Waiting for PostgreSQL..."
while ! pg_isready -h db -p 5432 -U postgres > /dev/null 2>&1; do
    echo "⏳ Waiting..."
    sleep 2
done
echo "✅ PostgreSQL is ready!"
sleep 3

echo "🔄 Preparing database..."

python3 - << 'PYEOF'
import os, sys
from sqlalchemy import create_engine, text

# Eski revision ID → yangi revision ID xaritasi
OLD_TO_NEW = {
    '001_initial':                       'rev_001',
    '002_add_usd_fields':                'rev_002',
    '003_add_product_usd_color':         'rev_003',
    '004_add_telegram_id':               'rev_004',
    '005_add_edit_tracking':             'rev_005',
    '006_add_user_language':             'rev_006',
    '007_add_expenses':                  'rev_007',
    '008_add_supplier_transactions':     'rev_008',
    '009_supplier_purchase_integration': 'rev_009',
}

url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/gayratstroy_db')
engine = create_engine(url)

with engine.connect() as conn:
    # 1. alembic_version jadvali borligini tekshirish
    has_version_table = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='alembic_version'"
    )).scalar()

    has_roles_table = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='roles'"
    )).scalar()

    print(f"  roles table: {'YES' if has_roles_table else 'NO'}")
    print(f"  alembic_version table: {'YES' if has_version_table else 'NO'}")

    if has_version_table:
        # 2. Ustun kengligini oshirish
        try:
            conn.execute(text(
                "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)"
            ))
            conn.commit()
            print("  ✅ version_num column → VARCHAR(64)")
        except Exception as e:
            conn.rollback()
            print(f"  ℹ️  version_num already wide: {e}")

        # 3. Joriy version ni o'qish
        row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).fetchone()
        current = row[0] if row else None
        print(f"  current version: {current or 'NONE'}")

        if current and current in OLD_TO_NEW:
            # Eski ID → yangi ID ga o'zgartirish
            new_id = OLD_TO_NEW[current]
            conn.execute(text(
                "UPDATE alembic_version SET version_num = :new WHERE version_num = :old"
            ), {"new": new_id, "old": current})
            conn.commit()
            print(f"  ✅ Migrated version ID: '{current}' → '{new_id}'")
        elif current and current.startswith('rev_'):
            print(f"  ✅ Version ID already new format: '{current}'")

            # Jadvallar bor lekin version eski bo'lsa — to'g'irlash
            # supplier_transactions bor → rev_008 gacha o'tgan
            # contact_phone ustuni yo'q → rev_010 kelmagan
            try:
                has_supplier_tx = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='supplier_transactions'"
                )).scalar()
                has_contact_phone = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_name='sales' AND column_name='contact_phone'"
                )).scalar()
                has_expenses = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='expenses'"
                )).scalar()
                has_purchase_orders = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='purchase_orders'"
                )).scalar()

                # Asl version ni aniqlash
                detected = current
                if has_purchase_orders:
                    detected = 'rev_009'
                elif has_supplier_tx:
                    detected = 'rev_008'
                elif has_expenses:
                    detected = 'rev_007'

                if has_contact_phone:
                    detected = 'rev_010'

                if detected != current:
                    conn.execute(text(
                        "UPDATE alembic_version SET version_num = :v"
                    ), {"v": detected})
                    conn.commit()
                    print(f"  ✅ Auto-corrected version: '{current}' → '{detected}'")
            except Exception as e:
                print(f"  ⚠️  Version detection error: {e}")
        elif current is None and has_roles_table:
            # alembic_version bo'sh lekin jadvallar bor
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('rev_006')"))
            conn.commit()
            print("  ✅ Inserted rev_006 into empty alembic_version")

    elif has_roles_table:
        # alembic_version jadvali yo'q, lekin roles bor — yangi jadval yaratib stamp qilamiz
        print("  ⚠️  No alembic_version table — will stamp after upgrade")
        # Bu holatda alembic stamp ishlaydi
        os.system("alembic stamp rev_006")
        print("  ✅ Stamped to rev_006")
    else:
        print("  🆕 Fresh database — full migration will run")

print("✅ Database preparation complete")
PYEOF

echo "🔄 Running migrations..."
alembic upgrade head

echo "🔄 Seeding database..."
python3 -c "
from database.seed import seed_all
from database import db
try:
    s = db.get_session_direct()
    seed_all(s)
    s.close()
    print('✅ Seeding done')
except Exception as e:
    print(f'⚠️  Seeding skipped: {e}')
" || true

echo "🚀 Starting server..."
exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload
