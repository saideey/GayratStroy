"""
Database seed script.
Creates initial data for the system:
- Default roles with permissions
- Standard units of measure
- System settings
- Expense categories
"""

from decimal import Decimal
from sqlalchemy.orm import Session

from .models import (
    Role, RoleType, PermissionType,
    UnitOfMeasure,
    SystemSetting,
    ExpenseCategory,
    SMSTemplate,
    Warehouse,
)


def seed_roles(session: Session):
    """Create default system roles."""
    
    # Director - full access
    director = Role(
        name="director",
        display_name="Direktor",
        description="To'liq kirish huquqi - barcha modullar va sozlamalar",
        role_type=RoleType.DIRECTOR,
        permissions=[p.value for p in PermissionType],  # All permissions
        max_discount_percent=100,
        is_system=True,
        is_active=True,
    )
    
    # Seller - sales focused
    seller_permissions = [
        PermissionType.PRODUCT_VIEW.value,
        PermissionType.WAREHOUSE_VIEW.value,
        PermissionType.SALE_VIEW.value,
        PermissionType.SALE_CREATE.value,
        PermissionType.SALE_DISCOUNT.value,
        PermissionType.SALE_DEBT.value,
        PermissionType.CUSTOMER_VIEW.value,
        PermissionType.CUSTOMER_CREATE.value,
        PermissionType.CUSTOMER_EDIT.value,
        PermissionType.REPORT_SALES.value,
    ]
    
    seller = Role(
        name="seller",
        display_name="Sotuvchi",
        description="Sotuv, qoldiq ko'rish, chegirma berish, qarz yozish",
        role_type=RoleType.SELLER,
        permissions=seller_permissions,
        max_discount_percent=15,  # Maximum 15% discount
        is_system=True,
        is_active=True,
    )
    
    # Warehouse Manager
    warehouse_permissions = [
        PermissionType.PRODUCT_VIEW.value,
        PermissionType.PRODUCT_CREATE.value,
        PermissionType.PRODUCT_EDIT.value,
        PermissionType.WAREHOUSE_VIEW.value,
        PermissionType.WAREHOUSE_INCOME.value,
        PermissionType.WAREHOUSE_OUTCOME.value,
        PermissionType.WAREHOUSE_TRANSFER.value,
        PermissionType.WAREHOUSE_INVENTORY.value,
        PermissionType.REPORT_WAREHOUSE.value,
    ]
    
    warehouse_manager = Role(
        name="warehouse_manager",
        display_name="Omborchi",
        description="Ombor boshqaruvi, kirim-chiqim, inventarizatsiya",
        role_type=RoleType.WAREHOUSE_MANAGER,
        permissions=warehouse_permissions,
        max_discount_percent=0,
        is_system=True,
        is_active=True,
    )
    
    # Accountant
    accountant_permissions = [
        PermissionType.SALE_VIEW.value,
        PermissionType.CUSTOMER_VIEW.value,
        PermissionType.REPORT_SALES.value,
        PermissionType.REPORT_WAREHOUSE.value,
        PermissionType.REPORT_FINANCE.value,
        PermissionType.REPORT_PROFIT.value,
        PermissionType.REPORT_EXPORT.value,
        PermissionType.FINANCE_VIEW.value,
    ]
    
    accountant = Role(
        name="accountant",
        display_name="Buxgalter",
        description="Moliyaviy hisobotlar, kassa, to'lovlar",
        role_type=RoleType.ACCOUNTANT,
        permissions=accountant_permissions,
        max_discount_percent=0,
        is_system=True,
        is_active=True,
    )
    
    # Check if roles exist
    existing = session.query(Role).filter(Role.is_system == True).first()
    if not existing:
        session.add_all([director, seller, warehouse_manager, accountant])
        session.commit()
        print("✅ Roles seeded successfully")
    else:
        print("ℹ️ Roles already exist, skipping")


def seed_units_of_measure(session: Session):
    """Create standard units of measure."""
    
    units = [
        # Weight units
        UnitOfMeasure(
            name="Kilogramm",
            symbol="kg",
            uom_type="weight",
            base_factor=1,
            decimal_places=2,
            is_integer_only=False,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Tonna",
            symbol="t",
            uom_type="weight",
            base_factor=1000,  # 1 tonna = 1000 kg
            decimal_places=3,
            is_integer_only=False,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Gramm",
            symbol="g",
            uom_type="weight",
            base_factor=Decimal("0.001"),  # 1 gramm = 0.001 kg
            decimal_places=0,
            is_integer_only=False,
            is_active=True,
        ),
        
        # Length units
        UnitOfMeasure(
            name="Metr",
            symbol="m",
            uom_type="length",
            base_factor=1,
            decimal_places=2,
            is_integer_only=False,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Santimetr",
            symbol="sm",
            uom_type="length",
            base_factor=Decimal("0.01"),
            decimal_places=0,
            is_integer_only=False,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Millimetr",
            symbol="mm",
            uom_type="length",
            base_factor=Decimal("0.001"),
            decimal_places=0,
            is_integer_only=False,
            is_active=True,
        ),
        
        # Area units
        UnitOfMeasure(
            name="Kvadrat metr",
            symbol="m²",
            uom_type="area",
            base_factor=1,
            decimal_places=2,
            is_integer_only=False,
            is_active=True,
        ),
        
        # Volume units
        UnitOfMeasure(
            name="Kub metr",
            symbol="m³",
            uom_type="volume",
            base_factor=1,
            decimal_places=3,
            is_integer_only=False,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Litr",
            symbol="l",
            uom_type="volume",
            base_factor=Decimal("0.001"),  # 1 litr = 0.001 m³
            decimal_places=2,
            is_integer_only=False,
            is_active=True,
        ),
        
        # Piece units
        UnitOfMeasure(
            name="Dona",
            symbol="dona",
            uom_type="piece",
            base_factor=1,
            decimal_places=0,
            is_integer_only=True,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Pochka",
            symbol="pochka",
            uom_type="piece",
            base_factor=1,  # Conversion set per product
            decimal_places=0,
            is_integer_only=True,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Quti",
            symbol="quti",
            uom_type="piece",
            base_factor=1,
            decimal_places=0,
            is_integer_only=True,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Rulon",
            symbol="rulon",
            uom_type="piece",
            base_factor=1,
            decimal_places=0,
            is_integer_only=True,
            is_active=True,
        ),
        UnitOfMeasure(
            name="Bog'lam",
            symbol="bog'lam",
            uom_type="piece",
            base_factor=1,
            decimal_places=0,
            is_integer_only=True,
            is_active=True,
        ),
    ]
    
    # Check if UOMs exist
    existing = session.query(UnitOfMeasure).first()
    if not existing:
        session.add_all(units)
        session.commit()
        print("✅ Units of measure seeded successfully")
    else:
        print("ℹ️ Units of measure already exist, skipping")


def seed_system_settings(session: Session):
    """Create default system settings."""
    
    settings = [
        # General settings
        SystemSetting(
            key="company_name",
            value="G'ayrat Stroy House",
            value_type="string",
            category="general",
            description="Kompaniya nomi",
            is_public=True,
        ),
        SystemSetting(
            key="company_phone",
            value="",
            value_type="string",
            category="general",
            description="Kompaniya telefon raqami",
            is_public=True,
        ),
        SystemSetting(
            key="company_address",
            value="",
            value_type="string",
            category="general",
            description="Kompaniya manzili",
            is_public=True,
        ),

        # Sales settings
        SystemSetting(
            key="max_seller_discount",
            value="15",
            value_type="number",
            category="sales",
            description="Sotuvchi berishi mumkin bo'lgan maksimal chegirma foizi",
            is_public=False,
        ),
        SystemSetting(
            key="allow_negative_stock_sales",
            value="false",
            value_type="boolean",
            category="sales",
            description="Manfiy qoldiqda sotishga ruxsat",
            is_public=False,
        ),
        SystemSetting(
            key="require_customer_for_debt",
            value="true",
            value_type="boolean",
            category="sales",
            description="Qarzga sotishda mijoz majburiymi",
            is_public=False,
        ),

        # SMS settings
        SystemSetting(
            key="sms_enabled",
            value="false",
            value_type="boolean",
            category="sms",
            description="SMS xabarnomalar yoqilganmi",
            is_public=False,
        ),
        SystemSetting(
            key="sms_provider",
            value="eskiz",
            value_type="string",
            category="sms",
            description="SMS provayder (eskiz, playmobile)",
            is_public=False,
        ),
        SystemSetting(
            key="sms_api_key",
            value="",
            value_type="string",
            category="sms",
            description="SMS API kaliti",
            is_public=False,
        ),
        SystemSetting(
            key="sms_on_sale",
            value="true",
            value_type="boolean",
            category="sms",
            description="Sotuvdan keyin SMS yuborish",
            is_public=False,
        ),
        SystemSetting(
            key="sms_on_debt_reminder",
            value="true",
            value_type="boolean",
            category="sms",
            description="Qarz eslatmasi uchun SMS",
            is_public=False,
        ),

        # Stock settings
        SystemSetting(
            key="low_stock_alert_enabled",
            value="true",
            value_type="boolean",
            category="warehouse",
            description="Kam qoldiq ogohlantirishini yoqish",
            is_public=False,
        ),
        SystemSetting(
            key="telegram_alerts_enabled",
            value="false",
            value_type="boolean",
            category="notifications",
            description="Telegram xabarnomalarini yoqish",
            is_public=False,
        ),
        SystemSetting(
            key="telegram_bot_token",
            value="",
            value_type="string",
            category="notifications",
            description="Telegram bot tokeni",
            is_public=False,
        ),

        # Currency settings
        SystemSetting(
            key="default_currency",
            value="UZS",
            value_type="string",
            category="finance",
            description="Asosiy valyuta",
            is_public=True,
        ),
        SystemSetting(
            key="usd_rate",
            value="12500",
            value_type="number",
            category="finance",
            description="USD kursi",
            is_public=True,
        ),
    ]

    # Check if settings exist
    existing = session.query(SystemSetting).first()
    if not existing:
        session.add_all(settings)
        session.commit()
        print("✅ System settings seeded successfully")
    else:
        print("ℹ️ System settings already exist, skipping")


def seed_expense_categories(session: Session):
    """Create default expense categories."""

    categories = [
        ExpenseCategory(name="Ish haqi", description="Xodimlar ish haqi"),
        ExpenseCategory(name="Ijara", description="Ombor va do'kon ijarasi"),
        ExpenseCategory(name="Kommunal xizmatlar", description="Elektr, suv, gaz"),
        ExpenseCategory(name="Transport", description="Yuk tashish xarajatlari"),
        ExpenseCategory(name="Xo'jalik", description="Xo'jalik mollari"),
        ExpenseCategory(name="Reklama", description="Reklama va marketing"),
        ExpenseCategory(name="Ta'mirlash", description="Ta'mirlash xarajatlari"),
        ExpenseCategory(name="Soliq", description="Soliqlar"),
        ExpenseCategory(name="Boshqa", description="Boshqa xarajatlar"),
    ]

    existing = session.query(ExpenseCategory).first()
    if not existing:
        session.add_all(categories)
        session.commit()
        print("✅ Expense categories seeded successfully")
    else:
        print("ℹ️ Expense categories already exist, skipping")


def seed_sms_templates(session: Session):
    """Create default SMS templates."""

    templates = [
        SMSTemplate(
            name="Sotuv yakunlandi",
            code="sale_complete",
            template_text="Hurmatli {customer_name}, sizning {amount} so'mlik xaridingiz uchun rahmat! G'ayrat Stroy House",
            variables=["customer_name", "amount"],
            is_active=True,
        ),
        SMSTemplate(
            name="Qarz eslatmasi",
            code="debt_reminder",
            template_text="Hurmatli {customer_name}, sizning {debt_amount} so'm qarzingiz mavjud. Iltimos to'lovni amalga oshiring. G'ayrat Stroy House",
            variables=["customer_name", "debt_amount"],
            is_active=True,
        ),
        SMSTemplate(
            name="To'lov qabul qilindi",
            code="payment_received",
            template_text="Hurmatli {customer_name}, {amount} so'mlik to'lovingiz qabul qilindi. Qolgan qarz: {remaining_debt} so'm. G'ayrat Stroy House",
            variables=["customer_name", "amount", "remaining_debt"],
            is_active=True,
        ),
    ]
    
    existing = session.query(SMSTemplate).first()
    if not existing:
        session.add_all(templates)
        session.commit()
        print("✅ SMS templates seeded successfully")
    else:
        print("ℹ️ SMS templates already exist, skipping")


def seed_default_warehouse(session: Session):
    """Create default warehouse."""
    
    existing = session.query(Warehouse).first()
    if not existing:
        warehouse = Warehouse(
            name="Asosiy Ombor",
            code="WH-01",
            address="",
            is_active=True,
            is_main=True,
        )
        session.add(warehouse)
        session.commit()
        print("✅ Default warehouse seeded successfully")
    else:
        print("ℹ️ Warehouse already exists, skipping")


def seed_admin_user(session: Session):
    """Create default admin user."""
    from core.security import get_password_hash
    from .models import User
    
    existing = session.query(User).filter(User.username == "admin").first()
    if not existing:
        # Get director role
        director_role = session.query(Role).filter(Role.name == "director").first()
        if director_role:
            admin = User(
                username="admin",
                email="admin@metall.uz",
                password_hash=get_password_hash("admin123"),
                first_name="Admin",
                last_name="Director",
                phone="+998901234567",
                role_id=director_role.id,
                is_active=True,
                is_blocked=False,
            )
            session.add(admin)
            session.commit()
            print("✅ Admin user seeded successfully (login: admin, password: admin123)")
    else:
        print("ℹ️ Admin user already exists, skipping")


def seed_all(session: Session):
    """Run all seed functions."""
    print("\n🌱 Starting database seeding...\n")
    
    seed_roles(session)
    seed_units_of_measure(session)
    seed_system_settings(session)
    seed_expense_categories(session)
    seed_sms_templates(session)
    seed_default_warehouse(session)
    seed_admin_user(session)
    
    print("\n✅ Database seeding completed!\n")


if __name__ == "__main__":
    from .connection import db
    
    with db.get_session() as session:
        seed_all(session)
