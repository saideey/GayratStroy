// Auth types
export interface User {
  id: number
  username: string
  email?: string
  first_name: string
  last_name: string
  phone?: string
  avatar_url?: string
  role_id: number
  role_name: string
  role_type: string
  permissions: string[]
  max_discount_percent: number
  assigned_warehouse_id?: number
  assigned_warehouse_name?: string
  language?: string  // uz, ru, uz_cyrl
}

export interface Role {
  id: number
  name: string
  display_name: string
  permissions: string[]
}

export interface LoginCredentials {
  username: string  // Changed from 'login' to 'username'
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthResponse {
  success: boolean
  message: string
  user: User
  tokens: TokenResponse
}

// Product types
export interface UOMConversion {
  id?: number
  uom_id: number
  uom_name: string
  uom_symbol: string
  conversion_factor: number
  sale_price?: number
  vip_price?: number
  is_default_sale_uom?: boolean
  is_base?: boolean
  stock_quantity?: number  // Stock in this UOM
}

export interface Product {
  id: number
  name: string
  article?: string
  barcode?: string
  category_id?: number
  category_name?: string
  base_uom_id: number
  base_uom_symbol: string
  base_uom_name?: string
  cost_price: number
  cost_price_usd?: number  // Cost in USD for dynamic rate calculation
  sale_price: number
  sale_price_usd?: number  // Sale price in USD
  vip_price?: number
  vip_price_usd?: number  // VIP price in USD
  color?: string  // HEX color code
  is_favorite?: boolean  // Tez-tez sotiladigan
  sort_order?: number  // Tartib
  image_url?: string
  is_active: boolean
  current_stock?: number
  uom_conversions?: UOMConversion[]
}

export interface Category {
  id: number
  name: string
  slug: string
  parent_id?: number
  children?: Category[]
  is_active: boolean
}

export interface UnitOfMeasure {
  id: number
  name: string
  symbol: string
  uom_type: string
}

// Customer types
export interface Customer {
  id: number
  name: string
  company_name?: string
  phone: string
  phone_secondary?: string
  telegram_id?: string
  email?: string
  address?: string
  customer_type: 'REGULAR' | 'VIP' | 'WHOLESALE'
  current_debt: number
  advance_balance: number
  credit_limit: number
  total_purchases: number
  is_active: boolean
  manager_id?: number
  manager_name?: string  // Kassir ismi
}

// POS / Sale types
export interface CartItem {
  id: string // unique cart item ID
  product_id: number
  product_name: string
  quantity: number
  uom_id: number
  uom_symbol: string
  uom_name?: string
  conversion_factor: number
  base_uom_id?: number
  base_uom_symbol?: string
  cost_price: number // Kelish narxi (base UOM uchun)
  original_price: number // Asl sotuv narxi
  unit_price: number // Hozirgi narx (chegirmadan keyin)
  discount_percent?: number
  discount_amount?: number
  total_price?: number
  available_stock?: number
}

export interface PaymentMethod {
  type: 'CASH' | 'CARD' | 'TRANSFER' | 'DEBT'
  amount: number
}

export interface SaleCreate {
  warehouse_id: number
  customer_id?: number
  items: SaleItemCreate[]
  final_total?: number
  payments: PaymentCreate[]
  notes?: string
}

export interface SaleItemCreate {
  product_id: number
  quantity: number
  uom_id: number
  unit_price?: number
}

export interface PaymentCreate {
  payment_type: string
  amount: number
}

export interface Sale {
  id: number
  sale_number: string
  sale_date: string
  customer_id?: number
  customer_name?: string
  seller_name: string
  subtotal: number
  discount_amount: number
  discount_percent: number
  total_amount: number
  paid_amount: number
  debt_amount: number
  payment_status: 'PENDING' | 'PARTIAL' | 'PAID' | 'DEBT' | 'CANCELLED'
  items_count: number
  is_cancelled: boolean
  created_at: string
}

// Stock types
export interface Stock {
  id: number
  product_id: number
  product_name: string
  product_article?: string
  warehouse_id: number
  warehouse_name: string
  quantity: number
  base_uom_symbol: string
  reserved_quantity: number
  available_quantity: number
  average_cost: number
  total_value: number
  min_stock_level: number
  is_below_minimum: boolean
}

export interface Warehouse {
  id: number
  name: string
  code?: string
  address?: string
  is_main: boolean
  is_active: boolean
  total_value?: number
}

// Quick product button for POS
export interface QuickProduct {
  id: number
  product_id: number
  name: string
  price: number
  color: string
  position: number
}

// API Response types
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T[]
  total: number
  page: number
  per_page: number
}

// Dashboard stats
export interface DailySummary {
  date: string
  total_sales: number
  total_amount: number
  total_paid: number
  total_debt: number
  total_discount: number
  gross_profit: number
  payment_breakdown: Record<string, number>
}
