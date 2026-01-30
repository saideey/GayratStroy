#!/usr/bin/env python3
"""
Admin parolini tiklash scripti.

Foydalanish:
    python reset_admin_password.py <yangi_parol>

Misol:
    python reset_admin_password.py MyNewPassword123
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API'))

from passlib.context import CryptContext
import psycopg2

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash parol."""
    return pwd_context.hash(password)

def reset_admin_password(new_password: str):
    """Admin parolini tiklash."""
    
    # Database connection settings (from .env)
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'metall_basa')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        
        # Hash the new password
        hashed_password = get_password_hash(new_password)
        
        # Update admin password
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s, 
                failed_login_attempts = 0,
                is_blocked = false
            WHERE username = 'admin'
            RETURNING id, username, first_name, last_name
        """, (hashed_password,))
        
        result = cursor.fetchone()
        
        if result:
            conn.commit()
            print(f"✅ Admin paroli muvaffaqiyatli tiklandi!")
            print(f"   ID: {result[0]}")
            print(f"   Username: {result[1]}")
            print(f"   Ism: {result[2]} {result[3]}")
            print(f"   Yangi parol: {new_password}")
        else:
            print("❌ Admin foydalanuvchi topilmadi!")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        sys.exit(1)

def list_all_users():
    """Barcha foydalanuvchilarni ko'rsatish."""
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'metall_basa')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.username, u.first_name, u.last_name, r.name as role_name, u.is_active
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.is_deleted = false
            ORDER BY u.id
        """)
        
        users = cursor.fetchall()
        
        print("\n📋 Barcha foydalanuvchilar:")
        print("-" * 70)
        print(f"{'ID':<5} {'Username':<15} {'Ism':<20} {'Role':<15} {'Status'}")
        print("-" * 70)
        
        for user in users:
            status = "✅ Faol" if user[5] else "❌ Nofaol"
            print(f"{user[0]:<5} {user[1]:<15} {user[2]} {user[3]:<10} {user[4]:<15} {status}")
        
        print("-" * 70)
        print(f"Jami: {len(users)} ta foydalanuvchi")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")

def reset_user_password(username: str, new_password: str):
    """Istalgan foydalanuvchi parolini tiklash."""
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'metall_basa')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        
        hashed_password = get_password_hash(new_password)
        
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s, 
                failed_login_attempts = 0,
                is_blocked = false
            WHERE username = %s AND is_deleted = false
            RETURNING id, username, first_name, last_name
        """, (hashed_password, username.lower()))
        
        result = cursor.fetchone()
        
        if result:
            conn.commit()
            print(f"✅ Parol muvaffaqiyatli tiklandi!")
            print(f"   ID: {result[0]}")
            print(f"   Username: {result[1]}")
            print(f"   Ism: {result[2]} {result[3]}")
            print(f"   Yangi parol: {new_password}")
        else:
            print(f"❌ '{username}' foydalanuvchi topilmadi!")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("🔐 Metall Basa - Parol Tiklash Scripti")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nFoydalanish:")
        print("  python reset_admin_password.py --list              # Barcha userlarni ko'rish")
        print("  python reset_admin_password.py admin <parol>       # Admin parolini tiklash")
        print("  python reset_admin_password.py <username> <parol>  # User parolini tiklash")
        print("\nMisol:")
        print("  python reset_admin_password.py admin MyNewPass123")
        print("  python reset_admin_password.py kassir Kassir123")
        sys.exit(0)
    
    if sys.argv[1] == '--list':
        list_all_users()
    elif len(sys.argv) == 3:
        username = sys.argv[1]
        new_password = sys.argv[2]
        
        if len(new_password) < 6:
            print("❌ Parol kamida 6 ta belgidan iborat bo'lishi kerak!")
            sys.exit(1)
        
        if username.lower() == 'admin':
            reset_admin_password(new_password)
        else:
            reset_user_password(username, new_password)
    else:
        print("❌ Noto'g'ri argumentlar!")
        print("Yordam uchun: python reset_admin_password.py")
