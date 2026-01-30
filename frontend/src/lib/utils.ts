import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format number as currency (UZS) with spaces
 */
export function formatMoney(amount: number | string, showCurrency = true): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) return '0'
  
  // Format with proper spacing (240000 → 240 000)
  const formatted = Math.round(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  
  return showCurrency ? `${formatted} so'm` : formatted
}

/**
 * Format number with spaces (1 000 000)
 */
export function formatNumber(num: number | string, decimals: number = 0): string {
  const n = typeof num === 'string' ? parseFloat(num) : num
  if (isNaN(n)) return '0'
  
  // Format with proper spacing
  const parts = n.toFixed(decimals).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  return parts.join('.')
}

/**
 * Format number for input display (with spaces)
 */
export function formatInputNumber(num: number | string): string {
  const n = typeof num === 'string' ? parseFloat(num) : num
  if (isNaN(n) || n === 0) return ''
  
  // Format with proper spacing
  const formatted = Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  return formatted
}

/**
 * Format date (DD.MM.YYYY)
 */
export function formatDate(date: string | Date, includeTime = false): string {
  const d = typeof date === 'string' ? new Date(date) : date
  
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  
  if (includeTime) {
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    return `${day}.${month}.${year} ${hours}:${minutes}`
  }
  
  return `${day}.${month}.${year}`
}

/**
 * Format date (DD.MM.YYYY)
 */
export function formatDateTashkent(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  
  return `${day}.${month}.${year}`
}

/**
 * Format time (HH:MM)
 */
export function formatTimeTashkent(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  
  return `${hours}:${minutes}`
}

/**
 * Format date and time (DD.MM.YYYY HH:MM)
 */
export function formatDateTimeTashkent(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  
  return `${day}.${month}.${year} ${hours}:${minutes}`
}

/**
 * Format phone number
 */
export function formatPhone(phone: string): string {
  // Remove non-digits
  const digits = phone.replace(/\D/g, '')
  
  // Format as +998 XX XXX XX XX
  if (digits.length === 12 && digits.startsWith('998')) {
    return `+${digits.slice(0, 3)} ${digits.slice(3, 5)} ${digits.slice(5, 8)} ${digits.slice(8, 10)} ${digits.slice(10)}`
  }
  
  return phone
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * Parse number from string (handles Uzbek format with spaces)
 */
export function parseNumber(value: string): number {
  const cleaned = value.replace(/\s/g, '').replace(',', '.')
  return parseFloat(cleaned) || 0
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Check if stock is low
 */
export function isLowStock(current: number, minimum: number): boolean {
  return current < minimum
}

/**
 * Get stock status color
 */
export function getStockStatusColor(current: number, minimum: number): string {
  if (current <= 0) return 'text-danger'
  if (current < minimum) return 'text-warning'
  return 'text-success'
}

/**
 * Get payment status label
 */
export function getPaymentStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    PENDING: 'Kutilmoqda',
    PARTIAL: 'Qisman',
    PAID: "To'langan",
    DEBT: 'Qarzga',
    CANCELLED: 'Bekor qilingan',
  }
  return labels[status] || status
}

/**
 * Get payment status color
 */
export function getPaymentStatusColor(status: string): string {
  const colors: Record<string, string> = {
    PENDING: 'bg-gray-100 text-gray-800',
    PARTIAL: 'bg-warning/10 text-warning-dark',
    PAID: 'bg-success/10 text-success-dark',
    DEBT: 'bg-danger/10 text-danger',
    CANCELLED: 'bg-gray-100 text-gray-500',
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

/**
 * Truncate text
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

/**
 * Sleep function for delays
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
