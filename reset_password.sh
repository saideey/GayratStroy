#!/bin/bash
# =====================================================
# Metall Basa - Admin Parolini Tiklash
# =====================================================
# 
# Bu script Docker container ichida ishlaydi
# 
# Foydalanish:
#   ./reset_password.sh                    # Barcha userlarni ko'rish
#   ./reset_password.sh admin MyNewPass    # Admin parolini tiklash
#   ./reset_password.sh kassir Kassir123   # User parolini tiklash
#
# =====================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}🔐 Metall Basa - Parol Tiklash${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check if running in project directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Bu scriptni metall_basa papkasidan ishga tushiring!${NC}"
    exit 1
fi

# Function to list users
list_users() {
    echo -e "\n${GREEN}📋 Barcha foydalanuvchilar:${NC}"
    docker-compose exec -T db psql -U postgres -d metall_basa -c "
        SELECT u.id, u.username, u.first_name || ' ' || u.last_name as full_name, 
               r.name as role, 
               CASE WHEN u.is_active THEN '✅ Faol' ELSE '❌ Nofaol' END as status
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.is_deleted = false
        ORDER BY u.id;
    "
}

# Function to reset password
reset_password() {
    local username=$1
    local new_password=$2
    
    if [ ${#new_password} -lt 6 ]; then
        echo -e "${RED}❌ Parol kamida 6 ta belgidan iborat bo'lishi kerak!${NC}"
        exit 1
    fi
    
    # Generate bcrypt hash using Python in the API container
    echo -e "\n${YELLOW}🔄 Parol hashlanmoqda...${NC}"
    
    hashed=$(docker-compose exec -T api python -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('$new_password'))
")
    
    # Remove any whitespace/newlines
    hashed=$(echo "$hashed" | tr -d '\r\n ')
    
    echo -e "${YELLOW}🔄 Database yangilanmoqda...${NC}"
    
    result=$(docker-compose exec -T db psql -U postgres -d metall_basa -t -c "
        UPDATE users 
        SET password_hash = '$hashed',
            failed_login_attempts = 0,
            is_blocked = false
        WHERE username = '${username,,}' AND is_deleted = false
        RETURNING id, username, first_name, last_name;
    ")
    
    if [ -z "$result" ] || [ "$result" = " " ]; then
        echo -e "${RED}❌ '${username}' foydalanuvchi topilmadi!${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Parol muvaffaqiyatli tiklandi!${NC}"
        echo -e "   Username: ${username}"
        echo -e "   Yangi parol: ${new_password}"
    fi
}

# Main logic
if [ $# -eq 0 ]; then
    list_users
elif [ $# -eq 2 ]; then
    reset_password "$1" "$2"
else
    echo -e "${YELLOW}Foydalanish:${NC}"
    echo "  ./reset_password.sh                    # Barcha userlarni ko'rish"
    echo "  ./reset_password.sh admin MyNewPass    # Admin parolini tiklash"
    echo "  ./reset_password.sh kassir Kassir123   # User parolini tiklash"
fi
