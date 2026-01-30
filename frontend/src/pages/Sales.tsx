import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { 
  Search, Calendar, Filter, Loader2, Eye, Pencil, Trash2, 
  Receipt, User, DollarSign, CreditCard, Banknote, AlertTriangle,
  Info, X, Phone, Package, Printer, Edit3
} from 'lucide-react'
import toast from 'react-hot-toast'
import { 
  Button, Input, Card, CardContent, Badge,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription 
} from '@/components/ui'
import api from '@/services/api'
import { formatMoney, formatNumber, cn, formatDateTashkent, formatTimeTashkent, formatDateTimeTashkent } from '@/lib/utils'
import { useAuthStore, usePOSStore } from '@/stores'
import { useLanguage } from '@/contexts/LanguageContext'

interface Sale {
  id: number
  sale_number: string
  sale_date: string
  customer_id: number | null
  customer_name: string | null
  seller_id: number
  seller_name: string
  total_amount: number
  paid_amount: number
  debt_amount: number
  payment_status: string
  items_count: number
  is_cancelled: boolean
  created_at: string
  updated_at?: string
  updated_by?: string
  edit_reason?: string
  // Permission flags
  can_edit: boolean
  is_own_sale: boolean
}

interface SaleDetail {
  id: number
  sale_number: string
  sale_date: string
  customer_id: number | null
  customer_name: string | null
  customer_phone: string | null
  seller_id: number
  seller_name: string
  warehouse_id: number
  warehouse_name: string
  subtotal: number
  discount_amount: number
  discount_percent: number
  total_amount: number
  paid_amount: number
  debt_amount: number
  payment_status: string
  payment_type: string | null
  items: {
    id: number
    product_name: string
    quantity: number
    uom_symbol: string
    unit_price: number
    total_price: number
  }[]
  payments: {
    id: number
    payment_number: string
    payment_date: string
    payment_type: string
    amount: number
  }[]
  notes: string | null
  is_cancelled: boolean
  cancelled_reason: string | null
  cancelled_at: string | null
  cancelled_by: string | null
  created_at: string
  updated_at: string | null
  updated_by: string | null
  edit_reason: string | null
}

interface Customer {
  id: number
  name: string
  phone: string
}

export default function SalesPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { loadSaleForEdit, resetPOS } = usePOSStore()
  const { t } = useLanguage()
  const isDirector = user?.role_type === 'director'
  
  // Filters
  const today = new Date()
  const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
  const [startDate, setStartDate] = useState(firstDayOfMonth.toISOString().split('T')[0])
  const [endDate, setEndDate] = useState(today.toISOString().split('T')[0])
  const [searchQuery, setSearchQuery] = useState('')
  const [paymentStatus, setPaymentStatus] = useState<string>('')
  const [showCancelled, setShowCancelled] = useState(false)
  const [page, setPage] = useState(1)
  
  // Dialogs
  const [viewingSale, setViewingSale] = useState<SaleDetail | null>(null)
  const [deletingSale, setDeletingSale] = useState<{id: number, sale_number: string} | null>(null)
  const [deleteReason, setDeleteReason] = useState('')
  const [loadingEditSale, setLoadingEditSale] = useState<number | null>(null)

  // Fetch sales
  const { data: salesData, isLoading } = useQuery({
    queryKey: ['sales', startDate, endDate, paymentStatus, showCancelled, page],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append('start_date', startDate)
      params.append('end_date', endDate)
      params.append('page', page.toString())
      params.append('per_page', '20')
      params.append('is_cancelled', showCancelled.toString())
      if (paymentStatus) params.append('payment_status', paymentStatus)
      
      const response = await api.get(`/sales?${params}`)
      return response.data
    }
  })

  // View sale detail
  const viewSale = async (saleId: number) => {
    try {
      const response = await api.get(`/sales/${saleId}`)
      setViewingSale(response.data.data)
    } catch (error) {
      toast.error(t('saleLoadError'))
    }
  }

  // Edit sale - load data and redirect to POS
  const handleEditSale = async (saleId: number) => {
    setLoadingEditSale(saleId)
    try {
      const response = await api.get(`/sales/${saleId}`)
      const sale = response.data.data

      // Reset POS and load sale data
      resetPOS()

      loadSaleForEdit({
        id: sale.id,
        sale_number: sale.sale_number,
        customer: sale.customer_id ? {
          id: sale.customer_id,
          name: sale.customer_name,
          phone: sale.customer_phone || '',
          current_debt: 0
        } : null,
        warehouse_id: sale.warehouse_id,
        items: sale.items.map((item: any) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          quantity: item.quantity,
          uom_id: item.uom_id,
          uom_symbol: item.uom_symbol,
          unit_price: item.unit_price,
          original_price: item.original_price || item.unit_price
        })),
        subtotal: sale.subtotal,
        discount_amount: sale.discount_amount,
        final_total: sale.total_amount,
        paid_amount: sale.paid_amount
      })

      // Navigate to POS
      navigate('/pos')
      toast.success(`Sotuv #${sale.sale_number} tahrirlash uchun yuklandi`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Sotuvni yuklashda xatolik')
    } finally {
      setLoadingEditSale(null)
    }
  }

  // Delete sale mutation
  const deleteSaleMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: number, reason: string }) => {
      const response = await api.delete(`/sales/${id}?reason=${encodeURIComponent(reason)}&return_to_stock=true`)
      return response.data
    },
    onSuccess: () => {
      toast.success(t('saleDeletedSuccess'))
      queryClient.invalidateQueries({ queryKey: ['sales'] })
      setDeletingSale(null)
      setDeleteReason('')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || t('deleteError'))
    }
  })

  // Get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'paid':
        return <Badge variant="success">{t('paid')}</Badge>
      case 'partial':
        return <Badge variant="warning">{t('partial')}</Badge>
      case 'debt':
        return <Badge variant="danger">{t('onDebt')}</Badge>
      case 'pending':
        return <Badge variant="secondary">{t('pending')}</Badge>
      case 'cancelled':
        return <Badge variant="secondary">{t('cancelled')}</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  // Filter sales by search
  const filteredSales = salesData?.data?.filter((sale: Sale) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      sale.sale_number.toLowerCase().includes(query) ||
      sale.customer_name?.toLowerCase().includes(query) ||
      sale.seller_name.toLowerCase().includes(query)
    )
  }) || []

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold">{t('sales')}</h1>
          <p className="text-sm text-text-secondary">
            {t('all')} {t('sales').toLowerCase()}
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            {/* Date Range */}
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-text-secondary" />
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-36"
              />
              <span>-</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-36"
              />
            </div>

            {/* Search */}
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
              <Input
                placeholder={t('search') + '...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Payment Status Filter */}
            <select
              value={paymentStatus}
              onChange={(e) => setPaymentStatus(e.target.value)}
              className="min-h-btn px-4 py-2 border-2 border-border rounded-pos"
            >
              <option value="">{t('all')}</option>
              <option value="paid">{t('paidStatus')}</option>
              <option value="partial">{t('partialStatus')}</option>
              <option value="debt">{t('onCredit')}</option>
            </select>

            {/* Show Cancelled */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showCancelled}
                onChange={(e) => setShowCancelled(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm">{t('cancelSale')}</span>
            </label>
          </div>

          {/* Summary */}
          {salesData?.summary && (
            <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-border">
              <div className="flex items-center gap-2">
                <Receipt className="w-4 h-4 text-primary" />
                <span className="text-sm text-text-secondary">{t('total')}:</span>
                <span className="font-semibold">{salesData.total}</span>
              </div>
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-success" />
                <span className="text-sm text-text-secondary">{t('sum')}:</span>
                <span className="font-semibold text-success">{formatMoney(salesData.summary.total_amount)}</span>
              </div>
              <div className="flex items-center gap-2">
                <Banknote className="w-4 h-4 text-primary" />
                <span className="text-sm text-text-secondary">{t('paid')}:</span>
                <span className="font-semibold text-primary">{formatMoney(salesData.summary.total_paid)}</span>
              </div>
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-danger" />
                <span className="text-sm text-text-secondary">{t('debt')}:</span>
                <span className="font-semibold text-danger">{formatMoney(salesData.summary.total_debt)}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info for Sellers */}
      {!isDirector && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium">Ma'lumot:</p>
            <p>Siz faqat <span className="font-semibold">oxirgi sotuvingizni</span> tahrirlashingiz yoki o'chirishingiz mumkin.
            Yangi sotuv qilganingizdan keyin avvalgi sotuvlarni o'zgartira olmaysiz.</p>
          </div>
        </div>
      )}

      {/* Sales Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : filteredSales.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-border">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium">№</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">{t('date')}</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">{t('customer')}</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">{t('seller')}</th>
                    <th className="px-4 py-3 text-right text-sm font-medium">{t('amount')}</th>
                    <th className="px-4 py-3 text-right text-sm font-medium">{t('paidAmount')}</th>
                    <th className="px-4 py-3 text-right text-sm font-medium">{t('debt')}</th>
                    <th className="px-4 py-3 text-center text-sm font-medium">{t('status')}</th>
                    <th className="px-4 py-3 text-center text-sm font-medium">{t('actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredSales.map((sale: Sale) => (
                    <tr key={sale.id} className={cn(
                      "hover:bg-gray-50",
                      sale.is_cancelled && "bg-gray-100 opacity-60",
                      sale.can_edit && !isDirector && "bg-green-50/50" // Highlight editable sale for sellers
                    )}>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm">{sale.sale_number}</span>
                          {sale.can_edit && !isDirector && !sale.is_cancelled && (
                            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-green-100 text-green-700">
                              {t('lastSale')}
                            </Badge>
                          )}
                        </div>
                        {sale.updated_by && (
                          <div className="text-xs text-warning flex items-center gap-1 mt-1">
                            <Pencil className="w-3 h-3" />
                            {t('edited')}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div>{formatDateTashkent(sale.sale_date)}</div>
                        <div className="text-xs text-text-secondary">
                          {formatTimeTashkent(sale.created_at)}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-medium">{sale.customer_name || t('unknownCustomer')}</p>
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary">
                        {sale.seller_name}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold">
                        {formatMoney(sale.total_amount)}
                      </td>
                      <td className="px-4 py-3 text-right text-success font-semibold">
                        {formatMoney(sale.paid_amount)}
                      </td>
                      <td className="px-4 py-3 text-right text-danger font-semibold">
                        {sale.debt_amount > 0 ? formatMoney(sale.debt_amount) : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {sale.is_cancelled ? (
                          <Badge variant="secondary">{t('cancelled')}</Badge>
                        ) : (
                          getStatusBadge(sale.payment_status)
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-1 h-8 w-8"
                            onClick={() => viewSale(sale.id)}
                          >
                            <Eye className="w-4 h-4 text-primary" />
                          </Button>
                          {/* Edit/Delete - Director yoki sotuvchining oxirgi sotuvi uchun */}
                          {sale.can_edit && !sale.is_cancelled && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="p-1 h-8 w-8"
                                onClick={() => handleEditSale(sale.id)}
                                disabled={loadingEditSale === sale.id}
                                title={isDirector ? "Tahrirlash" : "Oxirgi sotuvni tahrirlash"}
                              >
                                {loadingEditSale === sale.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin text-warning" />
                                ) : (
                                  <Edit3 className="w-4 h-4 text-warning" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="p-1 h-8 w-8"
                                onClick={() => setDeletingSale({ id: sale.id, sale_number: sale.sale_number })}
                                title={isDirector ? "O'chirish" : "Oxirgi sotuvni o'chirish"}
                              >
                                <Trash2 className="w-4 h-4 text-danger" />
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <Receipt className="w-16 h-16 mx-auto text-text-secondary opacity-50 mb-4" />
              <p className="text-text-secondary">{t('noSalesFound')}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {salesData && salesData.total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>
            {t('previous')}
          </Button>
          <span className="px-4">{page}</span>
          <Button variant="outline" onClick={() => setPage(page + 1)}>
            {t('next')}
          </Button>
        </div>
      )}

      {/* View Sale Dialog */}
      <Dialog open={!!viewingSale} onOpenChange={() => setViewingSale(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Receipt className="w-5 h-5 text-primary" />
              {t('sales')} #{viewingSale?.sale_number}
            </DialogTitle>
          </DialogHeader>

          {viewingSale && (
            <div className="space-y-4">
              {/* Sale Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-text-secondary">{t('date')}</p>
                  <p className="font-medium">{formatDateTashkent(viewingSale.sale_date)}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-text-secondary">{t('seller')}</p>
                  <p className="font-medium">{viewingSale.seller_name}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-text-secondary">{t('customer')}</p>
                  <p className="font-medium">{viewingSale.customer_name || t('unknownCustomer')}</p>
                  {viewingSale.customer_phone && (
                    <p className="text-sm text-text-secondary flex items-center gap-1">
                      <Phone className="w-3 h-3" />
                      {viewingSale.customer_phone}
                    </p>
                  )}
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-text-secondary">{t('warehouse')}</p>
                  <p className="font-medium">{viewingSale.warehouse_name}</p>
                </div>
              </div>

              {/* Items */}
              <div className="border border-border rounded-pos overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 font-medium">{t('products')}</div>
                <table className="w-full">
                  <thead className="bg-gray-50 border-t border-border">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm">{t('product')}</th>
                      <th className="px-4 py-2 text-right text-sm">{t('quantity')}</th>
                      <th className="px-4 py-2 text-right text-sm">{t('price')}</th>
                      <th className="px-4 py-2 text-right text-sm">{t('total')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {viewingSale.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-2">{item.product_name}</td>
                        <td className="px-4 py-2 text-right">{formatNumber(item.quantity)} {item.uom_symbol}</td>
                        <td className="px-4 py-2 text-right">{formatMoney(item.unit_price)}</td>
                        <td className="px-4 py-2 text-right font-semibold">{formatMoney(item.total_price)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Totals */}
              <div className="bg-gray-50 rounded-pos p-4 space-y-2">
                <div className="flex justify-between">
                  <span>{t('subtotal')}:</span>
                  <span className="font-semibold">{formatMoney(viewingSale.subtotal)}</span>
                </div>
                {viewingSale.discount_amount > 0 && (
                  <div className="flex justify-between text-success">
                    <span>{t('discount')} ({viewingSale.discount_percent.toFixed(1)}%):</span>
                    <span>-{formatMoney(viewingSale.discount_amount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold border-t border-border pt-2">
                  <span>{t('grandTotal')}:</span>
                  <span className="text-primary">{formatMoney(viewingSale.total_amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('paidAmount')}:</span>
                  <span className="text-success font-semibold">{formatMoney(viewingSale.paid_amount)}</span>
                </div>
                {viewingSale.debt_amount > 0 && (
                  <div className="flex justify-between">
                    <span>{t('debt')}:</span>
                    <span className="text-danger font-semibold">{formatMoney(viewingSale.debt_amount)}</span>
                  </div>
                )}
              </div>

              {/* Edit Info */}
              {viewingSale.updated_by && (
                <div className="bg-warning/10 p-3 rounded-lg text-sm">
                  <div className="flex items-start gap-2">
                    <Pencil className="w-4 h-4 text-warning mt-0.5" />
                    <div>
                      <p className="font-medium text-warning">{t('edited')}</p>
                      <p>{t('editedBy')}: {viewingSale.updated_by}</p>
                      <p>{t('editedWhen')}: {formatDateTimeTashkent(viewingSale.updated_at)}</p>
                      {viewingSale.edit_reason && <p>{t('reason')}: {viewingSale.edit_reason}</p>}
                    </div>
                  </div>
                </div>
              )}

              {/* Cancelled Info */}
              {viewingSale.is_cancelled && (
                <div className="bg-danger/10 p-3 rounded-lg text-sm">
                  <div className="flex items-start gap-2">
                    <X className="w-4 h-4 text-danger mt-0.5" />
                    <div>
                      <p className="font-medium text-danger">{t('cancelledStatus')}</p>
                      <p>{t('cancelledBy')}: {viewingSale.cancelled_by}</p>
                      <p>{t('cancelledWhen')}: {formatDateTimeTashkent(viewingSale.cancelled_at)}</p>
                      {viewingSale.cancelled_reason && <p>{t('reason')}: {viewingSale.cancelled_reason}</p>}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setViewingSale(null)}>{t('close')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Sale Dialog (Director only) */}
      <Dialog open={!!deletingSale} onOpenChange={() => { setDeletingSale(null); setDeleteReason(''); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-danger">
              <Trash2 className="w-5 h-5" />
              {t('deleteSaleTitle')}
            </DialogTitle>
            <DialogDescription>
              {t('sales')} #{deletingSale?.sale_number} {t('confirmDeleteSale')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-danger/10 p-3 rounded-lg text-sm">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-danger mt-0.5" />
                <div>
                  <p className="font-medium text-danger">{t('attentionWarning')}</p>
                  <p>{t('saleDeleteWarning')}</p>
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
            <Button variant="outline" onClick={() => { setDeletingSale(null); setDeleteReason(''); }}>{t('cancel')}</Button>
            <Button
              variant="danger"
              onClick={() => deletingSale && deleteSaleMutation.mutate({ id: deletingSale.id, reason: deleteReason })}
              disabled={deleteSaleMutation.isPending || !deleteReason.trim()}
            >
              {deleteSaleMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
              {t('delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}