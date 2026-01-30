"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    
    # ========================================
    # ROLES TABLE
    # ========================================
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role_type', sa.Enum('DIRECTOR', 'SELLER', 'WAREHOUSE_MANAGER', 'ACCOUNTANT', name='roletype'), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=False, default=[]),
        sa.Column('max_discount_percent', sa.Integer(), default=0),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_roles_name', 'roles', ['name'])
    op.create_index('ix_roles_role_type', 'roles', ['role_type'])
    
    # ========================================
    # UNITS OF MEASURE TABLE
    # ========================================
    op.create_table(
        'units_of_measure',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('uom_type', sa.String(50), nullable=False),
        sa.Column('base_factor', sa.Numeric(20, 10), nullable=False, default=1),
        sa.Column('decimal_places', sa.Integer(), default=2),
        sa.Column('is_integer_only', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('symbol'),
        sa.CheckConstraint('base_factor > 0', name='ck_uom_positive_factor')
    )
    op.create_index('ix_uom_type', 'units_of_measure', ['uom_type'])
    
    # ========================================
    # WAREHOUSES TABLE
    # ========================================
    op.create_table(
        'warehouses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_main', sa.Boolean(), default=False),
        sa.Column('allow_negative_stock', sa.Boolean(), default=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_warehouses_is_active', 'warehouses', ['is_active'])
    
    # ========================================
    # USERS TABLE
    # ========================================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_blocked', sa.Boolean(), default=False),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.Column('assigned_warehouse_id', sa.Integer(), nullable=True),
        sa.Column('last_login', sa.String(50), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('password_changed_at', sa.String(50), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['assigned_warehouse_id'], ['warehouses.id'])
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_phone', 'users', ['phone'])
    op.create_index('ix_users_role_id', 'users', ['role_id'])
    op.create_index('ix_users_assigned_warehouse', 'users', ['assigned_warehouse_id'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    
    # Add foreign key for warehouse manager
    op.create_foreign_key(
        'fk_warehouses_manager_id',
        'warehouses', 'users',
        ['manager_id'], ['id']
    )
    
    # ========================================
    # USER SESSIONS TABLE
    # ========================================
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('expires_at', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_token_hash', 'user_sessions', ['token_hash'])
    op.create_index('ix_user_sessions_is_active', 'user_sessions', ['is_active'])
    
    # ========================================
    # CATEGORIES TABLE
    # ========================================
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id']),
        sa.UniqueConstraint('name', 'parent_id', name='uq_category_name_parent')
    )
    op.create_index('ix_categories_slug', 'categories', ['slug'])
    op.create_index('ix_categories_parent_id', 'categories', ['parent_id'])
    op.create_index('ix_categories_is_active', 'categories', ['is_active'])
    
    # ========================================
    # PRODUCTS TABLE
    # ========================================
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('article', sa.String(100), nullable=True),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('base_uom_id', sa.Integer(), nullable=False),
        sa.Column('cost_price', sa.Numeric(20, 4), nullable=False, default=0),
        sa.Column('sale_price', sa.Numeric(20, 4), nullable=False, default=0),
        sa.Column('vip_price', sa.Numeric(20, 4), nullable=True),
        sa.Column('min_stock_level', sa.Numeric(20, 4), default=0),
        sa.Column('track_stock', sa.Boolean(), default=True),
        sa.Column('allow_negative_stock', sa.Boolean(), default=False),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('images', sa.Text(), nullable=True),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('manufacturer', sa.String(200), nullable=True),
        sa.Column('country_of_origin', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('is_service', sa.Boolean(), default=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article'),
        sa.UniqueConstraint('barcode'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['base_uom_id'], ['units_of_measure.id']),
        sa.CheckConstraint('cost_price >= 0', name='ck_product_cost_price_positive'),
        sa.CheckConstraint('sale_price >= 0', name='ck_product_sale_price_positive')
    )
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_article', 'products', ['article'])
    op.create_index('ix_products_barcode', 'products', ['barcode'])
    op.create_index('ix_products_category_id', 'products', ['category_id'])
    op.create_index('ix_products_base_uom_id', 'products', ['base_uom_id'])
    op.create_index('ix_products_is_active', 'products', ['is_active'])
    
    # ========================================
    # PRODUCT UOM CONVERSIONS TABLE
    # ========================================
    op.create_table(
        'product_uom_conversions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('uom_id', sa.Integer(), nullable=False),
        sa.Column('conversion_factor', sa.Numeric(20, 10), nullable=False),
        sa.Column('sale_price', sa.Numeric(20, 4), nullable=True),
        sa.Column('vip_price', sa.Numeric(20, 4), nullable=True),
        sa.Column('is_default_sale_uom', sa.Boolean(), default=False),
        sa.Column('is_default_purchase_uom', sa.Boolean(), default=False),
        sa.Column('is_integer_only', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uom_id'], ['units_of_measure.id']),
        sa.UniqueConstraint('product_id', 'uom_id', name='uq_product_uom'),
        sa.CheckConstraint('conversion_factor > 0', name='ck_product_uom_positive_factor')
    )
    op.create_index('ix_product_uom_product_id', 'product_uom_conversions', ['product_id'])
    op.create_index('ix_product_uom_uom_id', 'product_uom_conversions', ['uom_id'])
    
    # ========================================
    # PRODUCT PRICE HISTORY TABLE
    # ========================================
    op.create_table(
        'product_price_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('changed_by_id', sa.Integer(), nullable=False),
        sa.Column('price_type', sa.String(20), nullable=False),
        sa.Column('old_price', sa.Numeric(20, 4), nullable=True),
        sa.Column('new_price', sa.Numeric(20, 4), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'])
    )
    op.create_index('ix_price_history_product_id', 'product_price_history', ['product_id'])
    op.create_index('ix_price_history_created_at', 'product_price_history', ['created_at'])
    
    # ========================================
    # STOCK TABLE
    # ========================================
    op.create_table(
        'stock',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(20, 4), nullable=False, default=0),
        sa.Column('reserved_quantity', sa.Numeric(20, 4), nullable=False, default=0),
        sa.Column('average_cost', sa.Numeric(20, 4), nullable=False, default=0),
        sa.Column('last_purchase_cost', sa.Numeric(20, 4), nullable=False, default=0),
        sa.Column('last_stock_update', sa.String(50), nullable=True),
        sa.Column('last_inventory_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.UniqueConstraint('product_id', 'warehouse_id', name='uq_stock_product_warehouse')
    )
    op.create_index('ix_stock_product_id', 'stock', ['product_id'])
    op.create_index('ix_stock_warehouse_id', 'stock', ['warehouse_id'])
    op.create_index('ix_stock_quantity', 'stock', ['quantity'])
    
    # ========================================
    # STOCK MOVEMENTS TABLE
    # ========================================
    op.create_table(
        'stock_movements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.Enum(
            'PURCHASE', 'SALE', 'TRANSFER_IN', 'TRANSFER_OUT',
            'ADJUSTMENT_PLUS', 'ADJUSTMENT_MINUS', 'RETURN_FROM_CUSTOMER',
            'RETURN_TO_SUPPLIER', 'WRITE_OFF', 'INTERNAL_USE',
            name='movementtype'
        ), nullable=False),
        sa.Column('quantity', sa.Numeric(20, 4), nullable=False),
        sa.Column('uom_id', sa.Integer(), nullable=False),
        sa.Column('base_quantity', sa.Numeric(20, 4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(20, 4), default=0),
        sa.Column('total_cost', sa.Numeric(20, 4), default=0),
        sa.Column('stock_before', sa.Numeric(20, 4), nullable=False),
        sa.Column('stock_after', sa.Numeric(20, 4), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('related_warehouse_id', sa.Integer(), nullable=True),
        sa.Column('document_number', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['uom_id'], ['units_of_measure.id']),
        sa.ForeignKeyConstraint(['related_warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
        sa.CheckConstraint('quantity > 0', name='ck_movement_positive_quantity')
    )
    op.create_index('ix_stock_movements_product_id', 'stock_movements', ['product_id'])
    op.create_index('ix_stock_movements_warehouse_id', 'stock_movements', ['warehouse_id'])
    op.create_index('ix_stock_movements_type', 'stock_movements', ['movement_type'])
    op.create_index('ix_stock_movements_reference', 'stock_movements', ['reference_type', 'reference_id'])
    op.create_index('ix_stock_movements_created_at', 'stock_movements', ['created_at'])
    
    # ========================================
    # CUSTOMERS TABLE
    # ========================================
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('company_name', sa.String(300), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('phone_secondary', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('customer_type', sa.Enum('REGULAR', 'VIP', 'WHOLESALE', 'CONTRACTOR', name='customertype'),
                  nullable=False, default='REGULAR'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('login', sa.String(100), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('credit_limit', sa.Numeric(20, 4), default=0),
        sa.Column('current_debt', sa.Numeric(20, 4), default=0),
        sa.Column('advance_balance', sa.Numeric(20, 4), default=0),
        sa.Column('total_purchases', sa.Numeric(20, 4), default=0),
        sa.Column('total_purchases_count', sa.Integer(), default=0),
        sa.Column('last_purchase_date', sa.Date(), nullable=True),
        sa.Column('personal_discount_percent', sa.Numeric(5, 2), default=0),
        sa.Column('inn', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sms_enabled', sa.Boolean(), default=True),
        sa.Column('email_enabled', sa.Boolean(), default=False),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('login'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id']),
        sa.CheckConstraint('current_debt >= 0', name='ck_customer_debt_non_negative'),
        sa.CheckConstraint('advance_balance >= 0', name='ck_customer_advance_non_negative')
    )
    op.create_index('ix_customers_name', 'customers', ['name'])
    op.create_index('ix_customers_phone', 'customers', ['phone'])
    op.create_index('ix_customers_email', 'customers', ['email'])
    op.create_index('ix_customers_login', 'customers', ['login'])
    op.create_index('ix_customers_type', 'customers', ['customer_type'])
    op.create_index('ix_customers_is_active', 'customers', ['is_active'])
    op.create_index('ix_customers_manager_id', 'customers', ['manager_id'])
    
    # ========================================
    # EXPENSE CATEGORIES TABLE
    # ========================================
    op.create_table(
        'expense_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['parent_id'], ['expense_categories.id'])
    )
    op.create_index('ix_expense_categories_parent_id', 'expense_categories', ['parent_id'])
    
    # ========================================
    # CASH REGISTERS TABLE
    # ========================================
    op.create_table(
        'cash_registers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('current_balance', sa.Numeric(20, 4), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_open', sa.Boolean(), default=False),
        sa.Column('opened_at', sa.String(50), nullable=True),
        sa.Column('opened_by_id', sa.Integer(), nullable=True),
        sa.Column('opening_balance', sa.Numeric(20, 4), default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['opened_by_id'], ['users.id'])
    )
    op.create_index('ix_cash_registers_warehouse_id', 'cash_registers', ['warehouse_id'])
    op.create_index('ix_cash_registers_is_active', 'cash_registers', ['is_active'])
    
    # ========================================
    # SALES TABLE
    # ========================================
    op.create_table(
        'sales',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('sale_number', sa.String(50), nullable=False),
        sa.Column('sale_date', sa.Date(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('subtotal', sa.Numeric(20, 4), nullable=False),
        sa.Column('discount_amount', sa.Numeric(20, 4), default=0),
        sa.Column('discount_percent', sa.Numeric(5, 2), default=0),
        sa.Column('total_amount', sa.Numeric(20, 4), nullable=False),
        sa.Column('paid_amount', sa.Numeric(20, 4), default=0),
        sa.Column('debt_amount', sa.Numeric(20, 4), default=0),
        sa.Column('payment_status', sa.Enum('PENDING', 'PARTIAL', 'PAID', 'DEBT', 'CANCELLED', 'REFUNDED',
                                            name='paymentstatus'), nullable=False, default='PENDING'),
        sa.Column('payment_type', sa.Enum('CASH', 'CARD', 'TRANSFER', 'DEBT', 'MIXED',
                                          name='paymenttype'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('requires_delivery', sa.Boolean(), default=False),
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('delivery_cost', sa.Numeric(20, 4), default=0),
        sa.Column('is_vip_sale', sa.Boolean(), default=False),
        sa.Column('is_wholesale', sa.Boolean(), default=False),
        sa.Column('is_cancelled', sa.Boolean(), default=False),
        sa.Column('cancelled_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_by_id', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.String(50), nullable=True),
        sa.Column('discount_approved_by_id', sa.Integer(), nullable=True),
        sa.Column('sms_sent', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sale_number'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['cancelled_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['discount_approved_by_id'], ['users.id']),
        sa.CheckConstraint('total_amount >= 0', name='ck_sale_total_non_negative'),
        sa.CheckConstraint('discount_percent >= 0 AND discount_percent <= 100', name='ck_sale_discount_valid')
    )
    op.create_index('ix_sales_sale_number', 'sales', ['sale_number'])
    op.create_index('ix_sales_customer_id', 'sales', ['customer_id'])
    op.create_index('ix_sales_seller_id', 'sales', ['seller_id'])
    op.create_index('ix_sales_warehouse_id', 'sales', ['warehouse_id'])
    op.create_index('ix_sales_sale_date', 'sales', ['sale_date'])
    op.create_index('ix_sales_payment_status', 'sales', ['payment_status'])
    op.create_index('ix_sales_created_at', 'sales', ['created_at'])
    
    # ========================================
    # SALE ITEMS TABLE
    # ========================================
    op.create_table(
        'sale_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(20, 4), nullable=False),
        sa.Column('uom_id', sa.Integer(), nullable=False),
        sa.Column('base_quantity', sa.Numeric(20, 4), nullable=False),
        sa.Column('original_price', sa.Numeric(20, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(20, 4), nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), default=0),
        sa.Column('discount_amount', sa.Numeric(20, 4), default=0),
        sa.Column('total_price', sa.Numeric(20, 4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(20, 4), default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['uom_id'], ['units_of_measure.id']),
        sa.CheckConstraint('quantity > 0', name='ck_sale_item_positive_quantity'),
        sa.CheckConstraint('unit_price >= 0', name='ck_sale_item_price_non_negative')
    )
    op.create_index('ix_sale_items_sale_id', 'sale_items', ['sale_id'])
    op.create_index('ix_sale_items_product_id', 'sale_items', ['product_id'])
    
    # ========================================
    # PAYMENTS TABLE
    # ========================================
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('payment_number', sa.String(50), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('payment_type', sa.Enum('CASH', 'CARD', 'TRANSFER', 'DEBT', 'MIXED',
                                          name='paymenttype', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(20, 4), nullable=False),
        sa.Column('transaction_id', sa.String(100), nullable=True),
        sa.Column('cash_register_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_confirmed', sa.Boolean(), default=True),
        sa.Column('is_cancelled', sa.Boolean(), default=False),
        sa.Column('received_by_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_number'),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['cash_register_id'], ['cash_registers.id']),
        sa.ForeignKeyConstraint(['received_by_id'], ['users.id']),
        sa.CheckConstraint('amount > 0', name='ck_payment_positive_amount')
    )
    op.create_index('ix_payments_payment_number', 'payments', ['payment_number'])
    op.create_index('ix_payments_sale_id', 'payments', ['sale_id'])
    op.create_index('ix_payments_customer_id', 'payments', ['customer_id'])
    op.create_index('ix_payments_payment_date', 'payments', ['payment_date'])
    op.create_index('ix_payments_payment_type', 'payments', ['payment_type'])
    
    # ========================================
    # SUPPLIERS TABLE
    # ========================================
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('company_name', sa.String(300), nullable=True),
        sa.Column('contact_person', sa.String(200), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('phone_secondary', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('inn', sa.String(50), nullable=True),
        sa.Column('bank_account', sa.String(100), nullable=True),
        sa.Column('bank_name', sa.String(200), nullable=True),
        sa.Column('mfo', sa.String(20), nullable=True),
        sa.Column('credit_days', sa.Integer(), default=0),
        sa.Column('current_debt', sa.Numeric(20, 4), default=0),
        sa.Column('advance_balance', sa.Numeric(20, 4), default=0),
        sa.Column('product_categories', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), default=5),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_suppliers_name', 'suppliers', ['name'])
    op.create_index('ix_suppliers_phone', 'suppliers', ['phone'])
    op.create_index('ix_suppliers_is_active', 'suppliers', ['is_active'])
    
    # ========================================
    # PURCHASE ORDERS TABLE
    # ========================================
    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('order_number', sa.String(50), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('supplier_invoice', sa.String(100), nullable=True),
        sa.Column('supplier_invoice_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'APPROVED', 'ORDERED', 'PARTIAL', 'RECEIVED', 'CANCELLED',
                                    name='purchaseorderstatus'), nullable=False, default='DRAFT'),
        sa.Column('subtotal', sa.Numeric(20, 4), default=0),
        sa.Column('shipping_cost', sa.Numeric(20, 4), default=0),
        sa.Column('other_costs', sa.Numeric(20, 4), default=0),
        sa.Column('tax_amount', sa.Numeric(20, 4), default=0),
        sa.Column('total_amount', sa.Numeric(20, 4), nullable=False),
        sa.Column('paid_amount', sa.Numeric(20, 4), default=0),
        sa.Column('payment_status', sa.String(20), default='unpaid'),
        sa.Column('payment_due_date', sa.Date(), nullable=True),
        sa.Column('expected_date', sa.Date(), nullable=True),
        sa.Column('received_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.String(50), nullable=True),
        sa.Column('received_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['received_by_id'], ['users.id']),
        sa.CheckConstraint('total_amount >= 0', name='ck_po_total_non_negative')
    )
    op.create_index('ix_purchase_orders_order_number', 'purchase_orders', ['order_number'])
    op.create_index('ix_purchase_orders_supplier_id', 'purchase_orders', ['supplier_id'])
    op.create_index('ix_purchase_orders_warehouse_id', 'purchase_orders', ['warehouse_id'])
    op.create_index('ix_purchase_orders_status', 'purchase_orders', ['status'])
    op.create_index('ix_purchase_orders_order_date', 'purchase_orders', ['order_date'])
    
    # ========================================
    # PURCHASE ORDER ITEMS TABLE
    # ========================================
    op.create_table(
        'purchase_order_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('ordered_quantity', sa.Numeric(20, 4), nullable=False),
        sa.Column('uom_id', sa.Integer(), nullable=False),
        sa.Column('base_ordered_quantity', sa.Numeric(20, 4), nullable=False),
        sa.Column('received_quantity', sa.Numeric(20, 4), default=0),
        sa.Column('base_received_quantity', sa.Numeric(20, 4), default=0),
        sa.Column('unit_price', sa.Numeric(20, 4), nullable=False),
        sa.Column('total_price', sa.Numeric(20, 4), nullable=False),
        sa.Column('tax_percent', sa.Numeric(5, 2), default=0),
        sa.Column('tax_amount', sa.Numeric(20, 4), default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['uom_id'], ['units_of_measure.id']),
        sa.CheckConstraint('ordered_quantity > 0', name='ck_po_item_positive_quantity'),
        sa.CheckConstraint('unit_price >= 0', name='ck_po_item_price_non_negative')
    )
    op.create_index('ix_po_items_order_id', 'purchase_order_items', ['purchase_order_id'])
    op.create_index('ix_po_items_product_id', 'purchase_order_items', ['product_id'])
    
    # ========================================
    # SYSTEM SETTINGS TABLE
    # ========================================
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(20), default='string'),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('is_editable', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('ix_settings_key', 'system_settings', ['key'])
    op.create_index('ix_settings_category', 'system_settings', ['category'])
    
    # ========================================
    # AUDIT LOGS TABLE
    # ========================================
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=True),
        sa.Column('record_id', sa.Integer(), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_table', 'audit_logs', ['table_name'])
    op.create_index('ix_audit_logs_record', 'audit_logs', ['table_name', 'record_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # ========================================
    # SMS TEMPLATES TABLE
    # ========================================
    op.create_table(
        'sms_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('template_text', sa.Text(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_sms_templates_code', 'sms_templates', ['code'])
    
    # ========================================
    # SMS LOGS TABLE
    # ========================================
    op.create_table(
        'sms_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('provider_message_id', sa.String(100), nullable=True),
        sa.Column('sent_at', sa.String(50), nullable=True),
        sa.Column('delivered_at', sa.String(50), nullable=True),
        sa.Column('cost', sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['template_id'], ['sms_templates.id'])
    )
    op.create_index('ix_sms_logs_customer_id', 'sms_logs', ['customer_id'])
    op.create_index('ix_sms_logs_status', 'sms_logs', ['status'])
    op.create_index('ix_sms_logs_reference', 'sms_logs', ['reference_type', 'reference_id'])
    op.create_index('ix_sms_logs_created_at', 'sms_logs', ['created_at'])


def downgrade() -> None:
    """Drop all tables in reverse order."""
    
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_table('sms_logs')
    op.drop_table('sms_templates')
    op.drop_table('audit_logs')
    op.drop_table('system_settings')
    op.drop_table('purchase_order_items')
    op.drop_table('purchase_orders')
    op.drop_table('suppliers')
    op.drop_table('payments')
    op.drop_table('sale_items')
    op.drop_table('sales')
    op.drop_table('cash_registers')
    op.drop_table('expense_categories')
    op.drop_table('customers')
    op.drop_table('stock_movements')
    op.drop_table('stock')
    op.drop_table('product_price_history')
    op.drop_table('product_uom_conversions')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('user_sessions')
    
    # Remove foreign key before dropping users
    op.drop_constraint('fk_warehouses_manager_id', 'warehouses', type_='foreignkey')
    
    op.drop_table('users')
    op.drop_table('warehouses')
    op.drop_table('units_of_measure')
    op.drop_table('roles')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS roletype')
    op.execute('DROP TYPE IF EXISTS movementtype')
    op.execute('DROP TYPE IF EXISTS customertype')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymenttype')
    op.execute('DROP TYPE IF EXISTS purchaseorderstatus')
