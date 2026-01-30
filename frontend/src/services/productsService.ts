import api from './api'
import type { Product, Category, UnitOfMeasure, PaginatedResponse } from '@/types'

export interface ProductsParams {
  page?: number
  per_page?: number
  q?: string
  category_id?: number
  in_stock?: boolean
  is_active?: boolean
}

export const productsService = {
  async getProducts(params: ProductsParams = {}): Promise<PaginatedResponse<Product>> {
    const response = await api.get('/products', { params })
    return response.data
  },

  async getProduct(id: number): Promise<Product> {
    const response = await api.get(`/products/${id}`)
    return response.data.data || response.data
  },

  async getProductByBarcode(barcode: string): Promise<Product> {
    const response = await api.get(`/products/barcode/${barcode}`)
    return response.data.data || response.data
  },

  async createProduct(data: Partial<Product>): Promise<Product> {
    const response = await api.post('/products', data)
    return response.data
  },

  async updateProduct(id: number, data: Partial<Product>): Promise<Product> {
    const response = await api.patch(`/products/${id}`, data)
    return response.data
  },

  async deleteProduct(id: number): Promise<void> {
    await api.delete(`/products/${id}`)
  },

  // Categories
  async getCategories(): Promise<Category[]> {
    const response = await api.get('/products/categories')
    return response.data.data || response.data
  },

  async getCategoryTree(): Promise<Category[]> {
    const response = await api.get('/products/categories/tree')
    return response.data.data || response.data
  },

  async createCategory(data: { name: string; parent_id?: number }): Promise<Category> {
    const response = await api.post('/products/categories', data)
    return response.data.data || response.data
  },

  async deleteCategory(id: number): Promise<void> {
    await api.delete(`/products/categories/${id}`)
  },

  // Units of measure
  async getUOMs(): Promise<UnitOfMeasure[]> {
    const response = await api.get('/products/uom')
    // API returns {success: true, data: [...], count: N}
    const result = response.data?.data || response.data || []
    return Array.isArray(result) ? result : []
  },

  // Get product-specific UOM conversions
  async getProductUOMs(productId: number): Promise<any[]> {
    const response = await api.get(`/products/${productId}/uom-conversions`)
    const result = response.data?.data || response.data || []
    return Array.isArray(result) ? result : []
  },
}
