import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray } from 'react-hook-form'
import {
  Search, Plus, Package, Warehouse as WarehouseIcon, AlertTriangle,
  TrendingUp, Trash2, Calendar, DollarSign, History, Loader2, Filter, Download,
  Pencil, X, Info
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  Button, Input, Card, CardContent, Badge,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from '@/components/ui'
import { warehouseService, productsService } from '@/services'
import api from '@/services/api'
import { formatMoney, formatNumber, cn, formatDateTashkent, formatTimeTashkent, debounce } from '@/lib/utils'
import { useAuthStore } from '@/stores'
import { useLanguage } from '@/contexts/LanguageContext'
import type { Stock, Warehouse, Product } from '@/types'

interface IncomeItem {
  product_id: number
  quantity: number
  uom_id: number
  unit_price_usd: number // Dollarda narx
  unit_price_uzs: number // So'mda narx
}

type IncomeCurrency = 'USD' | 'UZS'

interface IncomeFormData {
  warehouse_id: number
  document_number?: string
  supplier_name?: string
  notes?: string
  items: IncomeItem[]
}

interface MovementEditData {
  id: number
  product_id: number
  product_name: string
  quantity: number
  uom_id: number
  uom_symbol: string
  unit_price: number
  unit_price_usd: number | null
  document_number: string
  supplier_name: string
  notes: string
}

type MovementFilter = 'all' | 'income' | 'outcome'

export default function WarehousePage() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const { t } = useLanguage()
  const isDirector = user?.role_type === 'director'

  const [searchQuery, setSearchQuery] = useState('')
  const [selectedWarehouse, setSelectedWarehouse] = useState<number | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
  const [showLowOnly, setShowLowOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [showIncomeDialog, setShowIncomeDialog] = useState(false)
  const [incomeCurrency, setIncomeCurrency] = useState<IncomeCurrency>('USD')
  const [activeTab, setActiveTab] = useState<'stock' | 'history'>('stock')

  // History filters
  const [movementFilter, setMovementFilter] = useState<MovementFilter>('all')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [showFilters, setShowFilters] = useState(false)
  const [movementSearchInput, setMovementSearchInput] = useState('')
  const [movementSearch, setMovementSearch] = useState('')

  // Search handler - Enter yoki button bosganda
  const handleMovementSearch = () => {
    setMovementSearch(movementSearchInput.trim())
    setPage(1)
  }

  // Clear search
  const clearMovementSearch = () => {
    setMovementSearchInput('')
    setMovementSearch('')
    setPage(1)
  }

  // Edit/Delete state
  const [editingMovement, setEditingMovement] = useState<MovementEditData | null>(null)
  const [deletingMovement, setDeletingMovement] = useState<{id: number, name: string} | null>(null)
  const [deleteReason, setDeleteReason] = useState('')

  // Fetch product UOMs for editing
  const { data: productUomsData } = useQuery({
    queryKey: ['product-uoms', editingMovement?.product_id],
    queryFn: async () => {
      if (!editingMovement?.product_id) return []
      const response = await productsService.getProductUOMs(editingMovement.product_id)
      return response
    },
    enabled: !!editingMovement?.product_id
  })
  const productUoms = Array.isArray(productUomsData) ? productUomsData : []

  const { register, control, handleSubmit, reset, watch } = useForm<IncomeFormData>({
    defaultValues: {
      warehouse_id: 1,
      items: [{ product_id: 0, quantity: 1, uom_id: 1, unit_price_usd: 0, unit_price_uzs: 0 }]
    }
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'items' })

  // Fetch exchange rate
  const { data: exchangeRateData } = useQuery({
    queryKey: ['exchange-rate'],
    queryFn: async () => {
      const response = await api.get('/settings/exchange-rate')
      return response.data
    },
  })
  const usdRate = exchangeRateData?.usd_rate || 12800

  // Fetch warehouses
  const { data: warehouses } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => warehouseService.getWarehouses(),
  })

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: productsService.getCategories,
  })

  // Fetch products for income form
  const { data: productsForSelect, isLoading: productsLoading } = useQuery({
    queryKey: ['products-for-select'],
    queryFn: async () => {
      const result = await productsService.getProducts({ per_page: 10000, is_active: true })
      return result
    },
  })

  // Safe products array - sort by name
  const productsList = (productsForSelect?.data || []).sort((a: Product, b: Product) =>
    a.name.localeCompare(b.name, 'uz')
  )

  // Fetch UOMs
  const { data: uomsResponse } = useQuery({
    queryKey: ['uoms'],
    queryFn: productsService.getUOMs,
  })
  const uoms = Array.isArray(uomsResponse) ? uomsResponse : []

  // Fetch stock
  const { data: stockData, isLoading } = useQuery({
    queryKey: ['stock', searchQuery, selectedWarehouse, selectedCategory, showLowOnly, page],
    queryFn: () => warehouseService.getStock({
      search: searchQuery || undefined,
      warehouse_id: selectedWarehouse || undefined,
      category_id: selectedCategory || undefined,
      below_minimum: showLowOnly || undefined,
      page,
      per_page: 20,
    }),
  })

  // Fetch stock movements (transaction history)
  const { data: movementsData, isLoading: loadingMovements, refetch: refetchMovements } = useQuery({
    queryKey: ['stock-movements', selectedWarehouse, movementFilter, startDate, endDate, movementSearch, page],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (selectedWarehouse) params.append('warehouse_id', selectedWarehouse.toString())

      // Movement type filter
      if (movementFilter === 'income') {
        params.append('movement_type', 'purchase')
      } else if (movementFilter === 'outcome') {
        params.append('movement_type', 'sale')
      }

      // Date filters
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)

      // Search filter - tovar nomi bo'yicha qidirish
      if (movementSearch && movementSearch.trim()) {
        params.append('q', movementSearch.trim())
      }

      params.append('page', page.toString())
      params.append('per_page', '50')

      const response = await api.get(`/warehouse/movements?${params}`)
      return response.data
    },
    enabled: activeTab === 'history',
    staleTime: 0, // Always refetch when parameters change
  })

  // Fetch low stock count
  const { data: lowStock } = useQuery({
    queryKey: ['low-stock'],
    queryFn: () => warehouseService.getLowStock(),
  })

  // Stock income mutation
  const stockIncome = useMutation({
    mutationFn: async (data: IncomeFormData & { currency: IncomeCurrency }) => {
      // Convert prices based on selected currency
      const itemsWithPrices = data.items
        .filter(item => item.product_id > 0 && item.quantity > 0)
        .map(item => {
          if (data.currency === 'USD') {
            // USD da kiritilgan - UZS ga convert qilish
            return {
              product_id: item.product_id,
              quantity: item.quantity,
              uom_id: item.uom_id,
              unit_price: item.unit_price_usd * usdRate, // Convert to UZS
              unit_price_usd: item.unit_price_usd,
              exchange_rate: usdRate
            }
          } else {
            // UZS da kiritilgan - USD ga convert qilish
            return {
              product_id: item.product_id,
              quantity: item.quantity,
              uom_id: item.uom_id,
              unit_price: item.unit_price_uzs, // Already in UZS
              unit_price_usd: item.unit_price_uzs / usdRate, // Convert to USD
              exchange_rate: usdRate
            }
          }
        })

      const response = await api.post('/warehouse/income', {
        ...data,
        items: itemsWithPrices,
        exchange_rate: usdRate
      })
      return response.data
    },
    onSuccess: () => {
      toast.success(t('incomeSuccess'))
      queryClient.invalidateQueries({ queryKey: ['stock'] })
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] })
      queryClient.invalidateQueries({ queryKey: ['low-stock'] })
      setShowIncomeDialog(false)
      setIncomeCurrency('USD')
      reset()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail.map((e: any) => e.msg).join(', ') || t('validationError'))
      } else {
        toast.error(typeof detail === 'string' ? detail : t('errorOccurred'))
      }
    },
  })

  // Edit movement mutation (Director only)
  const editMovement = useMutation({
    mutationFn: async (data: { id: number, quantity?: number, uom_id?: number, unit_price?: number, unit_price_usd?: number, document_number?: string, supplier_name?: string, notes?: string }) => {
      const params = new URLSearchParams()
      if (data.quantity !== undefined) params.append('quantity', data.quantity.toString())
      if (data.uom_id !== undefined) params.append('uom_id', data.uom_id.toString())
      if (data.unit_price !== undefined) params.append('unit_price', data.unit_price.toString())
      if (data.unit_price_usd !== undefined) params.append('unit_price_usd', data.unit_price_usd.toString())
      if (data.document_number !== undefined) params.append('document_number', data.document_number)
      if (data.supplier_name !== undefined) params.append('supplier_name', data.supplier_name)
      if (data.notes !== undefined) params.append('notes', data.notes)

      const response = await api.put(`/warehouse/movements/${data.id}?${params}`)
      return response.data
    },
    onSuccess: () => {
      toast.success(t('movementEdited'))
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] })
      queryClient.invalidateQueries({ queryKey: ['stock'] })
      setEditingMovement(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || t('editError'))
    }
  })

  // Delete movement mutation (Director only)
  const deleteMovement = useMutation({
    mutationFn: async ({ id, reason }: { id: number, reason: string }) => {
      const response = await api.delete(`/warehouse/movements/${id}?reason=${encodeURIComponent(reason)}`)
      return response.data
    },
    onSuccess: () => {
      toast.success(t('movementDeleted'))
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] })
      queryClient.invalidateQueries({ queryKey: ['stock'] })
      setDeletingMovement(null)
      setDeleteReason('')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || t('deleteError'))
    }
  })

  const onSubmit = (data: IncomeFormData) => {
    const validItems = data.items.filter(item => {
      if (incomeCurrency === 'USD') {
        return item.product_id > 0 && item.quantity > 0 && item.unit_price_usd > 0
      } else {
        return item.product_id > 0 && item.quantity > 0 && item.unit_price_uzs > 0
      }
    })
    if (validItems.length === 0) {
      toast.error(t('addAtLeastOneProduct'))
      return
    }
    stockIncome.mutate({ ...data, currency: incomeCurrency })
  }

  // Calculate total for income form based on currency
  const watchItems = watch('items')
  const incomeTotalUsd = incomeCurrency === 'USD'
    ? (watchItems?.reduce((sum, item) => sum + (item.quantity || 0) * (item.unit_price_usd || 0), 0) || 0)
    : (watchItems?.reduce((sum, item) => sum + (item.quantity || 0) * (item.unit_price_uzs || 0), 0) || 0) / usdRate

  const incomeTotalUzs = incomeCurrency === 'UZS'
    ? (watchItems?.reduce((sum, item) => sum + (item.quantity || 0) * (item.unit_price_uzs || 0), 0) || 0)
    : incomeTotalUsd * usdRate

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 lg:gap-4">
        <h1 className="text-xl lg:text-pos-xl font-bold">{t('warehouse')}</h1>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex items-center justify-center gap-2 px-3 lg:px-4 py-2 bg-primary/10 rounded-xl text-sm lg:text-base">
            <DollarSign className="w-4 h-4 lg:w-5 lg:h-5 text-primary" />
            <span className="font-semibold">1$ = {formatNumber(usdRate)} {t('sum')}</span>
          </div>
          <Button size="lg" variant="success" onClick={() => setShowIncomeDialog(true)} className="w-full sm:w-auto text-sm lg:text-base">
            <TrendingUp className="w-4 h-4 lg:w-5 lg:h-5 mr-2" />
            {t('stockIn')}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 lg:gap-4">
        {warehouses?.map((wh: Warehouse) => (
          <Card
            key={wh.id}
            className={cn('cursor-pointer transition-all', selectedWarehouse === wh.id && 'ring-2 ring-primary')}
            onClick={() => setSelectedWarehouse(selectedWarehouse === wh.id ? null : wh.id)}
          >
            <CardContent className="p-2.5 lg:p-4 flex flex-col lg:flex-row items-center gap-2 lg:gap-4">
              <div className="p-2 lg:p-3 bg-primary/10 rounded-xl">
                <WarehouseIcon className="w-5 h-5 lg:w-6 lg:h-6 text-primary" />
              </div>
              <div className="text-center lg:text-left">
                <p className="font-semibold text-sm lg:text-base">{wh.name}</p>
                <p className="text-xs lg:text-sm text-text-secondary truncate">{formatMoney(wh.total_value || 0)}</p>
              </div>
            </CardContent>
          </Card>
        ))}

        <Card
          className={cn('cursor-pointer transition-all border-warning', showLowOnly && 'ring-2 ring-warning')}
          onClick={() => setShowLowOnly(!showLowOnly)}
        >
          <CardContent className="p-2.5 lg:p-4 flex flex-col lg:flex-row items-center gap-2 lg:gap-4">
            <div className="p-2 lg:p-3 bg-warning/10 rounded-xl">
              <AlertTriangle className="w-5 h-5 lg:w-6 lg:h-6 text-warning" />
            </div>
            <div className="text-center lg:text-left">
              <p className="font-semibold text-sm lg:text-base">{t('lowStock')}</p>
              <p className="text-xs lg:text-sm text-danger font-bold">{lowStock?.data?.length || 0}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 lg:gap-2 border-b border-border overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveTab('stock')}
          className={cn(
            'px-4 lg:px-6 py-2.5 lg:py-3 font-medium border-b-2 transition-colors whitespace-nowrap text-sm lg:text-base',
            activeTab === 'stock' ? 'border-primary text-primary' : 'border-transparent hover:text-primary'
          )}
        >
          <Package className="w-4 h-4 lg:w-5 lg:h-5 inline mr-1.5 lg:mr-2" />
          {t('inventory')}
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={cn(
            'px-4 lg:px-6 py-2.5 lg:py-3 font-medium border-b-2 transition-colors whitespace-nowrap text-sm lg:text-base',
            activeTab === 'history' ? 'border-primary text-primary' : 'border-transparent hover:text-primary'
          )}
        >
          <History className="w-4 h-4 lg:w-5 lg:h-5 inline mr-1.5 lg:mr-2" />
          {t('movements')}
        </button>
      </div>

      {/* Stock Tab */}
      {activeTab === 'stock' && (
        <>
          {/* Filters */}
          <Card>
            <CardContent className="p-3 lg:p-4">
              <div className="flex flex-col sm:flex-row gap-2 lg:gap-4 items-stretch sm:items-center">
                <div className="flex-1">
                  <Input
                    icon={<Search className="w-4 h-4 lg:w-5 lg:h-5" />}
                    placeholder={t('searchProducts') + '...'}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="text-sm lg:text-base"
                  />
                </div>
                <select
                  className="min-h-[44px] lg:min-h-btn px-3 lg:px-4 py-2 lg:py-3 border-2 border-border rounded-xl text-sm lg:text-pos-base"
                  value={selectedCategory || ''}
                  onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
                >
                  <option value="">{t('allCategories')}</option>
                  {categories?.map((cat: any) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Stock List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[700px]">
                  <thead className="bg-gray-50 border-b border-border">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium">{t('product')}</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">{t('article')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium">{t('balance')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium">{t('avgCostUsd')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium">{t('avgCostUzs')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium">{t('sellingPrice')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium">{t('totalValue')}</th>
                      <th className="px-4 py-3 text-center text-sm font-medium">{t('status')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {stockData?.data?.map((stock: Stock) => {
                      // Mahsulotni topish va UOM konversiyalarini olish
                      const product = productsList.find((p: Product) => p.id === stock.product_id)
                      const uomConversions = product?.uom_conversions || []

                      return (
                      <tr key={stock.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <p className="font-medium">{stock.product_name}</p>
                        </td>
                        <td className="px-4 py-3 text-sm text-text-secondary">
                          {stock.product_article || '-'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {/* Asosiy UOM dagi qoldiq */}
                          <div className="font-semibold">
                            {formatNumber(stock.quantity, stock.quantity < 1 && stock.quantity > 0 ? 3 : 1)} {stock.base_uom_symbol}
                          </div>
                          {/* Boshqa UOM lardagi qoldiq */}
                          {uomConversions.length > 0 && stock.quantity > 0 && (
                            <div className="text-xs text-gray-500 mt-0.5 space-y-0.5">
                              {uomConversions.map((conv: any) => (
                                <div key={conv.uom_id}>
                                  ≈ {formatNumber(stock.quantity / conv.conversion_factor, 1)} {conv.uom_symbol}
                                </div>
                              ))}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right text-sm">
                          ${formatNumber(stock.average_cost / usdRate, 2)}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-warning">
                          {formatMoney(stock.average_cost)}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-success">
                          {formatMoney((productsList.find((p: Product) => p.id === stock.product_id)?.sale_price) || 0)}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold">
                          {formatMoney(stock.total_value)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {stock.is_below_minimum ? (
                            <Badge variant="danger">{t('low')}</Badge>
                          ) : stock.quantity === 0 ? (
                            <Badge variant="secondary">{t('outOfStock')}</Badge>
                          ) : (
                            <Badge variant="success">OK</Badge>
                          )}
                        </td>
                      </tr>
                    )})}
                  </tbody>
                </table>
              </div>

              {stockData?.data?.length === 0 && (
                <div className="text-center py-12">
                  <Package className="w-16 h-16 mx-auto text-text-secondary opacity-50 mb-4" />
                  <p className="text-text-secondary">{t('productsNotFound')}</p>
                </div>
              )}
            </Card>
          )}
        </>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <>
          {/* Search & Filter Panel */}
          <Card className="mb-4">
            <CardContent className="p-4 space-y-4">
              {/* Search Input */}
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={movementSearchInput}
                    onChange={(e) => setMovementSearchInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleMovementSearch()}
                    placeholder={t('Qidiruv: ') + '... (Olma, Kraska, ...)'}
                    className="w-full pl-10 pr-10 py-2.5 border border-border rounded-lg focus:outline-none focus:border-primary"
                  />
                  {movementSearchInput && (
                    <button
                      onClick={clearMovementSearch}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <Button
                  type="button"
                  onClick={handleMovementSearch}
                  className="px-4"
                >
                  <Search className="w-4 h-4 mr-1" />
                  {t('search')}
                </Button>
              </div>

              {/* Active search indicator */}
              {movementSearch && (
                <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg text-sm">
                  <span className="text-blue-700">
                    🔍 Qidiruv: "<strong>{movementSearch}</strong>"
                  </span>
                  <button
                    onClick={clearMovementSearch}
                    className="ml-auto text-blue-600 hover:text-blue-800 text-xs"
                  >
                    Tozalash
                  </button>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-4">
                {/* Movement Type Filter */}
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{t('movementType')}:</span>
                  <div className="flex rounded-lg border overflow-hidden">
                    <button
                      onClick={() => { setMovementFilter('all'); setPage(1) }}
                      className={cn(
                        "px-3 py-1.5 text-sm",
                        movementFilter === 'all' ? 'bg-primary text-white' : 'hover:bg-gray-100'
                      )}
                    >
                      {t('all')}
                    </button>
                    <button
                      onClick={() => { setMovementFilter('income'); setPage(1) }}
                      className={cn(
                        "px-3 py-1.5 text-sm border-l",
                        movementFilter === 'income' ? 'bg-green-600 text-white' : 'hover:bg-gray-100'
                      )}
                    >
                      {t('incomeType')}
                    </button>
                    <button
                      onClick={() => { setMovementFilter('outcome'); setPage(1) }}
                      className={cn(
                        "px-3 py-1.5 text-sm border-l",
                        movementFilter === 'outcome' ? 'bg-red-600 text-white' : 'hover:bg-gray-100'
                      )}
                    >
                      {t('soldType')}
                    </button>
                  </div>
                </div>

                {/* Date Range */}
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{t('date')}:</span>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => { setStartDate(e.target.value); setPage(1) }}
                    className="h-9 px-3 text-sm border rounded-lg"
                  />
                  <span className="text-gray-500">—</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => { setEndDate(e.target.value); setPage(1) }}
                    className="h-9 px-3 text-sm border rounded-lg"
                  />
                </div>

                {/* Clear Filters */}
                {(movementFilter !== 'all' || startDate || endDate) && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setMovementFilter('all')
                      setStartDate('')
                      setEndDate('')
                      setPage(1)
                    }}
                  >
                    {t('clearFilters')}
                  </Button>
                )}

                {/* Results count */}
                <div className="ml-auto text-sm text-gray-500">
                  {t('totalCount')}: {movementsData?.total || 0}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              {loadingMovements ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : movementsData?.data && movementsData.data.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-border">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium">{t('date')}</th>
                        <th className="px-4 py-3 text-left text-sm font-medium">{t('product')}</th>
                        <th className="px-4 py-3 text-right text-sm font-medium">{t('quantity')}</th>
                        <th className="px-4 py-3 text-right text-sm font-medium">{t('priceUsd')}</th>
                        <th className="px-4 py-3 text-right text-sm font-medium">{t('priceUzs')}</th>
                        <th className="px-4 py-3 text-right text-sm font-medium">{t('total')}</th>
                        <th className="px-4 py-3 text-left text-sm font-medium">{t('documentNo')}</th>
                        <th className="px-4 py-3 text-left text-sm font-medium">{t('supplier')}</th>
                        <th className="px-4 py-3 text-center text-sm font-medium">{t('movementType')}</th>
                        {isDirector && <th className="px-4 py-3 text-center text-sm font-medium">{t('actions')}</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {movementsData.data.map((movement: any) => {
                      const canEdit = ['purchase', 'adjustment_plus', 'adjustment_minus'].includes(movement.movement_type)
                      return (
                      <tr key={movement.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4 text-text-secondary" />
                            {formatDateTashkent(movement.created_at)}
                          </div>
                          <div className="text-xs text-text-secondary">
                            {formatTimeTashkent(movement.created_at)}
                          </div>
                          {movement.updated_at && movement.updated_by_name && (
                            <div className="text-xs text-warning mt-1 flex items-center gap-1">
                              <Pencil className="w-3 h-3" />
                              {movement.updated_by_name}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <p className="font-medium">{movement.product_name}</p>
                          <p className="text-xs text-text-secondary">{movement.product_article || ''}</p>
                        </td>
                        <td className="px-4 py-3 text-right font-semibold">
                          <span className={['purchase', 'transfer_in', 'adjustment_plus', 'return_from_customer'].includes(movement.movement_type) ? 'text-success' : 'text-danger'}>
                            {['purchase', 'transfer_in', 'adjustment_plus', 'return_from_customer'].includes(movement.movement_type) ? '+' : '-'}{formatNumber(movement.quantity)} {movement.uom_symbol}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-sm">
                          ${formatNumber(movement.unit_price_usd || (movement.unit_price / (movement.exchange_rate || usdRate)), 2)}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-warning">
                          {formatMoney(movement.unit_price)}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold">
                          {formatMoney(movement.total_price || movement.quantity * movement.unit_price)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {movement.document_number || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {movement.supplier_name || '-'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Badge variant={['purchase', 'transfer_in', 'adjustment_plus', 'return_from_customer'].includes(movement.movement_type) ? 'success' : 'danger'}>
                            {movement.movement_type === 'purchase' ? t('incomeType') :
                             movement.movement_type === 'sale' ? t('soldType') :
                             movement.movement_type === 'transfer_in' ? t('transferIn') :
                             movement.movement_type === 'transfer_out' ? t('transferOut') :
                             movement.movement_type === 'adjustment_plus' ? t('adjustmentPlus') :
                             movement.movement_type === 'adjustment_minus' ? t('adjustmentMinus') :
                             movement.movement_type === 'write_off' ? t('writeOff') : movement.movement_type}
                          </Badge>
                        </td>
                        {isDirector && (
                          <td className="px-4 py-3 text-center">
                            {canEdit ? (
                              <div className="flex items-center justify-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="p-1 h-8 w-8"
                                  onClick={() => setEditingMovement({
                                    id: movement.id,
                                    product_id: movement.product_id,
                                    product_name: movement.product_name,
                                    quantity: movement.quantity,
                                    uom_id: movement.uom_id,
                                    uom_symbol: movement.uom_symbol,
                                    unit_price: movement.unit_price,
                                    unit_price_usd: movement.unit_price_usd,
                                    document_number: movement.document_number || '',
                                    supplier_name: movement.supplier_name || '',
                                    notes: movement.notes || ''
                                  })}
                                >
                                  <Pencil className="w-4 h-4 text-primary" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="p-1 h-8 w-8"
                                  onClick={() => setDeletingMovement({ id: movement.id, name: movement.product_name })}
                                >
                                  <Trash2 className="w-4 h-4 text-danger" />
                                </Button>
                              </div>
                            ) : (
                              <span className="text-xs text-text-secondary">-</span>
                            )}
                          </td>
                        )}
                      </tr>
                    )})}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <History className="w-16 h-16 mx-auto text-text-secondary opacity-50 mb-4" />
                <p className="text-text-secondary">{t('movementHistoryNotFound')}</p>
              </div>
            )}
          </CardContent>
        </Card>
        </>
      )}

      {/* Pagination */}
      {((activeTab === 'stock' && stockData && stockData.total > 20) ||
        (activeTab === 'history' && movementsData && movementsData.total > 30)) && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>{t('previous')}</Button>
          <span className="px-4">{page}</span>
          <Button variant="outline" onClick={() => setPage(page + 1)}>{t('next')}</Button>
        </div>
      )}

      {/* Income Dialog */}
      <Dialog open={showIncomeDialog} onOpenChange={setShowIncomeDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto overflow-x-visible">
          <DialogHeader>
            <DialogTitle>{t('stockIncome')}</DialogTitle>
            <DialogDescription>{t('currentRateInfo')}: 1$ = {formatNumber(usdRate)} {t('sum')}</DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Currency Selection */}
            <div className="flex items-center justify-center gap-2 p-2 bg-gray-100 rounded-pos">
              <span className="text-sm font-medium mr-2">{t('currency')}:</span>
              <div className="flex rounded-lg overflow-hidden border-2 border-border">
                <button
                  type="button"
                  onClick={() => setIncomeCurrency('USD')}
                  className={`px-4 py-2 font-bold text-sm transition-all ${
                    incomeCurrency === 'USD'
                      ? 'bg-primary text-white'
                      : 'bg-white text-text-secondary hover:bg-gray-50'
                  }`}
                >
                  $ USD
                </button>
                <button
                  type="button"
                  onClick={() => setIncomeCurrency('UZS')}
                  className={`px-4 py-2 font-bold text-sm transition-all ${
                    incomeCurrency === 'UZS'
                      ? 'bg-success text-white'
                      : 'bg-white text-text-secondary hover:bg-gray-50'
                  }`}
                >
                  UZS {t('sum')}
                </button>
              </div>
            </div>

            {/* Warehouse & Document */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="font-medium">{t('warehouse')}</label>
                <select
                  {...register('warehouse_id', { valueAsNumber: true })}
                  className="w-full min-h-btn px-4 py-3 border-2 border-border rounded-pos"
                >
                  {warehouses?.map((wh: Warehouse) => (
                    <option key={wh.id} value={wh.id}>{wh.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="font-medium">{t('documentNo')}</label>
                <Input {...register('document_number')} placeholder={t('invoiceNo')} />
              </div>
              <div className="space-y-2">
                <label className="font-medium">{t('supplier')}</label>
                <Input {...register('supplier_name')} placeholder={t('supplierName')} />
              </div>
            </div>

            {/* Items */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="font-medium">{t('productsLabel')}</label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => append({ product_id: 0, quantity: 1, uom_id: 1, unit_price_usd: 0, unit_price_uzs: 0 })}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  {t('add')}
                </Button>
              </div>

              <div className="border border-border rounded-pos">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-sm font-medium">{t('product')}</th>
                      <th className="px-3 py-2 text-center text-sm font-medium w-32">{t('quantity')}</th>
                      <th className="px-3 py-2 text-center text-sm font-medium w-24">{t('measureUnit')}</th>
                      <th className="px-3 py-2 text-center text-sm font-medium w-36">
                        {t('price')} {incomeCurrency === 'USD' ? '($)' : '(UZS)'}
                      </th>
                      <th className="px-3 py-2 text-right text-sm font-medium w-36">
                        {t('total')} {incomeCurrency === 'USD' ? '($)' : '(UZS)'}
                      </th>
                      <th className="px-3 py-2 w-12"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {fields.map((field, index) => {
                      const item = watchItems?.[index]
                      const itemTotal = incomeCurrency === 'USD'
                        ? (item?.quantity || 0) * (item?.unit_price_usd || 0)
                        : (item?.quantity || 0) * (item?.unit_price_uzs || 0)
                      return (
                        <tr key={field.id}>
                          <td className="px-3 py-2 min-w-[200px]">
                            <select
                              {...register(`items.${index}.product_id`, { valueAsNumber: true })}
                              className="w-full px-2 py-2 border border-border rounded text-sm bg-white"
                            >
                              <option value={0}>
                                {productsLoading ? t('loading') : `${t('selectProduct')} (${productsList.length} ta)`}
                              </option>
                              {productsList.map((p: Product) => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                              ))}
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            <Input
                              type="number"
                              {...register(`items.${index}.quantity`, { valueAsNumber: true })}
                              className="text-center text-sm w-full"
                              placeholder="0"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <select
                              {...register(`items.${index}.uom_id`, { valueAsNumber: true })}
                              className="w-full px-2 py-2 border border-border rounded text-sm"
                            >
                              {uoms.map((uom: any) => (
                                <option key={uom.id} value={uom.id}>{uom.symbol}</option>
                              ))}
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            {incomeCurrency === 'USD' ? (
                              <div className="relative">
                                <span className="absolute left-2 top-1/2 -translate-y-1/2 text-text-secondary font-bold">$</span>
                                <Input
                                  type="number"
                                  step="0.01"
                                  {...register(`items.${index}.unit_price_usd`, { valueAsNumber: true })}
                                  className="text-center text-sm pl-6 w-full"
                                  placeholder="0.00"
                                />
                              </div>
                            ) : (
                              <Input
                                type="number"
                                step="1"
                                {...register(`items.${index}.unit_price_uzs`, { valueAsNumber: true })}
                                className="text-center text-sm w-full"
                                placeholder="0"
                              />
                            )}
                          </td>
                          <td className="px-3 py-2 text-right font-semibold text-success">
                            {incomeCurrency === 'USD'
                              ? `$${formatNumber(itemTotal, 2)}`
                              : formatMoney(itemTotal)
                            }
                          </td>
                          <td className="px-3 py-2">
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => remove(index)}
                              disabled={fields.length === 1}
                            >
                              <Trash2 className="w-4 h-4 text-danger" />
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <label className="font-medium">{t('notes')}</label>
              <Input {...register('notes')} placeholder={t('additionalInfo')} />
            </div>

            {/* Total */}
            <div className={`p-4 rounded-pos ${incomeCurrency === 'USD' ? 'bg-gradient-to-r from-primary/10 to-success/10' : 'bg-gradient-to-r from-success/10 to-primary/10'}`}>
              <div className="flex justify-between items-center">
                {incomeCurrency === 'USD' ? (
                  <>
                    <div>
                      <p className="text-sm text-text-secondary">{t('totalUsd')}:</p>
                      <p className="text-pos-xl font-bold text-primary">${formatNumber(incomeTotalUsd, 2)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-text-secondary">≈ {t('inUzs')}:</p>
                      <p className="text-pos-lg font-bold text-success">{formatMoney(incomeTotalUzs)}</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <p className="text-sm text-text-secondary">{t('totalUzs')}:</p>
                      <p className="text-pos-xl font-bold text-success">{formatMoney(incomeTotalUzs)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-text-secondary">≈ {t('inUsd')}:</p>
                      <p className="text-pos-lg font-bold text-primary">${formatNumber(incomeTotalUsd, 2)}</p>
                    </div>
                  </>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => { setShowIncomeDialog(false); setIncomeCurrency('USD'); }}>{t('cancel')}</Button>
              <Button type="submit" variant="success" disabled={stockIncome.isPending}>
                {stockIncome.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <TrendingUp className="w-4 h-4 mr-2" />}
                {t('saveIncome')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Movement Dialog (Director only) */}
      <Dialog open={!!editingMovement} onOpenChange={() => setEditingMovement(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pencil className="w-5 h-5 text-primary" />
              {t('editMovementTitle')}
            </DialogTitle>
            <DialogDescription>
              {editingMovement?.product_name}
            </DialogDescription>
          </DialogHeader>

          {editingMovement && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="font-medium text-sm">{t('quantity')}</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={editingMovement.quantity}
                    onChange={(e) => setEditingMovement({...editingMovement, quantity: parseFloat(e.target.value) || 0})}
                  />
                </div>
                <div className="space-y-2">
                  <label className="font-medium text-sm">{t('unit')}</label>
                  <select
                    className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    value={editingMovement.uom_id}
                    onChange={(e) => {
                      const availableUoms = productUoms.length > 0 ? productUoms : uoms
                      const selectedUom = availableUoms.find((u: any) => u.uom_id === parseInt(e.target.value) || u.id === parseInt(e.target.value))
                      setEditingMovement({
                        ...editingMovement,
                        uom_id: parseInt(e.target.value),
                        uom_symbol: selectedUom?.uom_symbol || selectedUom?.symbol || ''
                      })
                    }}
                  >
                    {productUoms.length > 0 ? (
                      productUoms.map((uom: any) => (
                        <option key={uom.uom_id} value={uom.uom_id}>
                          {uom.uom_name} ({uom.uom_symbol}) - koef: {uom.conversion_factor}
                        </option>
                      ))
                    ) : (
                      uoms.map((uom: any) => (
                        <option key={uom.id} value={uom.id}>{uom.name} ({uom.symbol})</option>
                      ))
                    )}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="font-medium text-sm">{t('priceUsd')}</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={editingMovement.unit_price_usd || ''}
                    onChange={(e) => setEditingMovement({
                      ...editingMovement,
                      unit_price_usd: parseFloat(e.target.value) || 0,
                      unit_price: (parseFloat(e.target.value) || 0) * usdRate
                    })}
                  />
                </div>
                <div className="space-y-2">
                  <label className="font-medium text-sm">{t('priceUzs')}</label>
                  <Input
                    type="number"
                    step="1"
                    value={editingMovement.unit_price}
                    onChange={(e) => setEditingMovement({...editingMovement, unit_price: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="font-medium text-sm">{t('documentNo')}</label>
                <Input
                  value={editingMovement.document_number}
                  onChange={(e) => setEditingMovement({...editingMovement, document_number: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="font-medium text-sm">{t('supplier')}</label>
                <Input
                  value={editingMovement.supplier_name}
                  onChange={(e) => setEditingMovement({...editingMovement, supplier_name: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="font-medium text-sm">{t('notes')}</label>
                <Input
                  value={editingMovement.notes}
                  onChange={(e) => setEditingMovement({...editingMovement, notes: e.target.value})}
                />
              </div>

              <div className="bg-warning/10 p-3 rounded-lg text-sm">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-warning mt-0.5" />
                  <p>{t('quantityChangeWarning')}</p>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingMovement(null)}>{t('cancel')}</Button>
            <Button
              variant="primary"
              onClick={() => editingMovement && editMovement.mutate({
                id: editingMovement.id,
                quantity: editingMovement.quantity,
                uom_id: editingMovement.uom_id,
                unit_price: editingMovement.unit_price,
                unit_price_usd: editingMovement.unit_price_usd || undefined,
                document_number: editingMovement.document_number,
                supplier_name: editingMovement.supplier_name,
                notes: editingMovement.notes
              })}
              disabled={editMovement.isPending}
            >
              {editMovement.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Pencil className="w-4 h-4 mr-2" />}
              {t('save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Movement Dialog (Director only) */}
      <Dialog open={!!deletingMovement} onOpenChange={() => { setDeletingMovement(null); setDeleteReason(''); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-danger">
              <Trash2 className="w-5 h-5" />
              {t('deleteMovementTitle')}
            </DialogTitle>
            <DialogDescription>
              <span className="font-semibold">{deletingMovement?.name}</span> {t('confirmDeleteMovement')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-danger/10 p-3 rounded-lg text-sm">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-danger mt-0.5" />
                <div>
                  <p className="font-medium text-danger">{t('attentionWarning')}</p>
                  <p>{t('deleteMovementWarning')}</p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="font-medium text-sm">{t('deleteReasonLabel')} *</label>
              <Input
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                placeholder={t('enterReasonRequired')}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setDeletingMovement(null); setDeleteReason(''); }}>{t('cancel')}</Button>
            <Button
              variant="danger"
              onClick={() => deletingMovement && deleteMovement.mutate({ id: deletingMovement.id, reason: deleteReason })}
              disabled={deleteMovement.isPending || !deleteReason.trim()}
            >
              {deleteMovement.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
              {t('delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}