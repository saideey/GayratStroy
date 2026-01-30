import api from './api'
import type { Stock, Warehouse, PaginatedResponse } from '@/types'

export interface StockParams {
  warehouse_id?: number
  category_id?: number
  below_minimum?: boolean
  out_of_stock?: boolean
  search?: string
  page?: number
  per_page?: number
}

export const warehouseService = {
  // Warehouses
  async getWarehouses(includeInactive = false): Promise<Warehouse[]> {
    const response = await api.get('/warehouse', { params: { include_inactive: includeInactive } })
    return response.data.data || response.data
  },

  async createWarehouse(data: Partial<Warehouse>): Promise<Warehouse> {
    const response = await api.post('/warehouse', data)
    return response.data.data
  },

  // Stock
  async getStock(params: StockParams = {}): Promise<PaginatedResponse<Stock> & { total_value: number }> {
    const response = await api.get('/warehouse/stock', { params })
    return response.data
  },

  async getLowStock(warehouseId?: number): Promise<Stock[]> {
    const params: any = {}
    if (warehouseId) params.warehouse_id = warehouseId
    const response = await api.get('/warehouse/stock/low', { params })
    return response.data.data
  },

  async getStockValue(warehouseId?: number): Promise<number> {
    const params: any = {}
    if (warehouseId) params.warehouse_id = warehouseId
    const response = await api.get('/warehouse/stock/value', { params })
    return response.data.total_value
  },

  // Stock income
  async stockIncome(data: {
    warehouse_id: number
    document_number?: string
    notes?: string
    items: {
      product_id: number
      quantity: number
      uom_id: number
      unit_price: number
    }[]
  }): Promise<void> {
    await api.post('/warehouse/income', data)
  },

  // Stock adjustment
  async stockAdjustment(data: {
    product_id: number
    warehouse_id: number
    quantity: number
    uom_id: number
    movement_type: string
    unit_cost?: number
    document_number?: string
    notes?: string
  }): Promise<void> {
    await api.post('/warehouse/adjustment', data)
  },

  // Movements
  async getMovements(params: {
    product_id?: number
    warehouse_id?: number
    movement_type?: string
    start_date?: string
    end_date?: string
    page?: number
    per_page?: number
  } = {}): Promise<any> {
    const response = await api.get('/warehouse/movements', { params })
    return response.data
  },

  // Transfers
  async createTransfer(data: {
    from_warehouse_id: number
    to_warehouse_id: number
    items: { product_id: number; quantity: number; uom_id: number }[]
    notes?: string
  }): Promise<void> {
    await api.post('/warehouse/transfer', data)
  },

  async completeTransfer(transferId: number): Promise<void> {
    await api.post(`/warehouse/transfer/${transferId}/complete`)
  },

  async cancelTransfer(transferId: number): Promise<void> {
    await api.post(`/warehouse/transfer/${transferId}/cancel`)
  },
}
