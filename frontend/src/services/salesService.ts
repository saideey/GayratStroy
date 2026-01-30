import api from './api'
import type { Sale, SaleCreate, PaginatedResponse, DailySummary } from '@/types'

export interface SalesParams {
  page?: number
  per_page?: number
  customer_id?: number
  seller_id?: number
  warehouse_id?: number
  payment_status?: string
  start_date?: string
  end_date?: string
  is_cancelled?: boolean
}

export const salesService = {
  async getSales(params: SalesParams = {}): Promise<PaginatedResponse<Sale> & { summary: any }> {
    const response = await api.get('/sales', { params })
    return response.data
  },

  async getSale(id: number): Promise<Sale> {
    const response = await api.get(`/sales/${id}`)
    return response.data.data
  },

  async createSale(data: SaleCreate): Promise<{ sale_number: string; id: number }> {
    const response = await api.post('/sales', data)
    return response.data.data
  },

  async quickSale(data: {
    warehouse_id: number
    customer_id?: number
    items: { product_id: number; quantity: number; uom_id: number; unit_price?: number }[]
    final_total?: number
    payment_type: string
    payment_amount: number
    notes?: string
  }): Promise<{ sale_number: string; total_amount: number; change: number }> {
    const response = await api.post('/sales/quick', data)
    return response.data.data
  },

  async addPayment(saleId: number, data: {
    payment_type: string
    amount: number
    notes?: string
  }): Promise<void> {
    await api.post(`/sales/${saleId}/payment`, data)
  },

  async cancelSale(saleId: number, data: {
    reason: string
    return_to_stock: boolean
  }): Promise<void> {
    await api.post(`/sales/${saleId}/cancel`, data)
  },

  async getDailySummary(date?: string, warehouseId?: number, sellerId?: number): Promise<DailySummary> {
    const params: any = {}
    if (date) params.sale_date = date
    if (warehouseId) params.warehouse_id = warehouseId
    if (sellerId) params.seller_id = sellerId
    const response = await api.get('/sales/daily-summary', { params })
    return response.data.data
  },

  async getReceipt(saleId: number): Promise<any> {
    const response = await api.get(`/sales/${saleId}/receipt`)
    return response.data.data
  },
}
