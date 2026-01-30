import api from './api'
import type { Customer, PaginatedResponse } from '@/types'

export interface CustomersParams {
  page?: number
  per_page?: number
  q?: string
  customer_type?: string
  has_debt?: boolean
  is_active?: boolean
}

export const customersService = {
  async getCustomers(params: CustomersParams = {}): Promise<PaginatedResponse<Customer>> {
    const response = await api.get('/customers', { params })
    return response.data
  },

  async getCustomer(id: number): Promise<Customer> {
    const response = await api.get(`/customers/${id}`)
    return response.data
  },

  async createCustomer(data: Partial<Customer>): Promise<Customer> {
    const response = await api.post('/customers', data)
    return response.data
  },

  async updateCustomer(id: number, data: Partial<Customer>): Promise<Customer> {
    const response = await api.patch(`/customers/${id}`, data)
    return response.data
  },

  async deleteCustomer(id: number): Promise<void> {
    await api.delete(`/customers/${id}`)
  },

  async getDebtors(minDebt?: number, sellerId?: number): Promise<{ data: Customer[]; total_debt: number }> {
    const params: any = {}
    if (minDebt) params.min_debt = minDebt
    if (sellerId) params.seller_id = sellerId
    const response = await api.get('/customers/debtors', { params })
    return response.data
  },

  async payDebt(customerId: number, data: {
    amount: number
    payment_type: string
    description?: string
  }): Promise<{ current_debt: number; advance_balance: number }> {
    const response = await api.post(`/customers/${customerId}/pay-debt`, data)
    return response.data
  },

  async addAdvance(customerId: number, data: {
    amount: number
    payment_type: string
    description?: string
  }): Promise<{ advance_balance: number }> {
    const response = await api.post(`/customers/${customerId}/add-advance`, data)
    return response.data
  },

  async getDebtHistory(customerId: number, page = 1, perPage = 20): Promise<any> {
    const response = await api.get(`/customers/${customerId}/debt-history`, {
      params: { page, per_page: perPage }
    })
    return response.data
  },
}
