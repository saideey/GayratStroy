import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Calendar, Download, TrendingUp, DollarSign, Package, 
  Users, FileSpreadsheet, FileText, Loader2, Settings, User, ShoppingCart, CreditCard, Banknote, Phone, Building, ChevronDown, ChevronUp
} from 'lucide-react'
import toast from 'react-hot-toast'
import { Button, Input, Card, CardContent, Badge } from '@/components/ui'
import api from '@/services/api'
import { formatMoney, formatNumber, cn, formatDateTashkent, formatDateTimeTashkent } from '@/lib/utils'
import { useLanguage } from '@/contexts/LanguageContext'

export default function ReportsPage() {
  const { t } = useLanguage()
  
  // Date filters
  const today = new Date()
  const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
  
  const [startDate, setStartDate] = useState(firstDayOfMonth.toISOString().split('T')[0])
  const [endDate, setEndDate] = useState(today.toISOString().split('T')[0])
  const [activeTab, setActiveTab] = useState<'profit' | 'sales' | 'sellers' | 'export'>('profit')
  const [selectedSellerId, setSelectedSellerId] = useState<number | ''>('')
  const [expandedSection, setExpandedSection] = useState<string | null>('sales')

  // Fetch profit report
  const { data: profitData, isLoading: loadingProfit, refetch: refetchProfit } = useQuery({
    queryKey: ['profit-report', startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/reports/profit', {
        params: { start_date: startDate, end_date: endDate }
      })
      return response.data
    },
    enabled: activeTab === 'profit',
  })

  // Fetch sales summary
  const { data: salesData, isLoading: loadingSales, refetch: refetchSales } = useQuery({
    queryKey: ['sales-summary', startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/reports/sales-summary', {
        params: { start_date: startDate, end_date: endDate }
      })
      return response.data
    },
    enabled: activeTab === 'sales',
  })

  // Fetch exchange rate
  const { data: exchangeRateData } = useQuery({
    queryKey: ['exchange-rate'],
    queryFn: async () => {
      const response = await api.get('/settings/exchange-rate')
      return response.data
    },
  })

  // Fetch all sellers summary
  const { data: sellersSummary, isLoading: loadingSellersSummary } = useQuery({
    queryKey: ['sellers-summary', startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/reports/sellers-summary', {
        params: { start_date: startDate, end_date: endDate }
      })
      return response.data
    },
    enabled: activeTab === 'sellers',
  })

  // Fetch specific seller stats
  const { data: sellerStats, isLoading: loadingSellerStats } = useQuery({
    queryKey: ['seller-stats', selectedSellerId, startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/reports/seller-stats', {
        params: { seller_id: selectedSellerId, start_date: startDate, end_date: endDate }
      })
      return response.data
    },
    enabled: activeTab === 'sellers' && !!selectedSellerId,
  })

  // Download Excel report
  const handleDownloadExcel = async (type: string) => {
    try {
      toast.loading(t('reportPreparing'))
      
      const response = await api.get(`/reports/excel/${type}`, {
        params: { start_date: startDate, end_date: endDate },
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${type}_${startDate}_${endDate}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      toast.dismiss()
      toast.success(t('reportDownloaded'))
    } catch (error) {
      toast.dismiss()
      toast.error(t('reportError'))
    }
  }

  // Download PDF report
  const handleDownloadPDF = async (type: string) => {
    try {
      toast.loading(t('reportPreparing'))
      
      const response = await api.get(`/reports/pdf/${type}`, {
        params: { start_date: startDate, end_date: endDate },
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${type}_${startDate}_${endDate}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      toast.dismiss()
      toast.success(t('reportDownloaded'))
    } catch (error) {
      toast.dismiss()
      toast.error(t('reportError'))
    }
  }

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 lg:gap-4">
        <h1 className="text-xl lg:text-pos-xl font-bold">{t('reports')}</h1>
        
        {/* Date Filters */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 lg:gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 lg:w-5 lg:h-5 text-text-secondary hidden sm:block" />
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="flex-1 sm:w-32 lg:w-40 text-sm lg:text-base"
            />
            <span className="text-text-secondary">-</span>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="flex-1 sm:w-32 lg:w-40 text-sm lg:text-base"
            />
          </div>
          
          {exchangeRateData && (
            <Badge variant="secondary" className="text-sm lg:text-pos-base justify-center">
              $ = {formatNumber(exchangeRateData.usd_rate)} {t('sum')}
            </Badge>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveTab('profit')}
          className={cn(
            'px-3 lg:px-6 py-2.5 lg:py-3 font-medium border-b-4 transition-colors whitespace-nowrap text-sm lg:text-base',
            activeTab === 'profit'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          )}
        >
          <TrendingUp className="w-4 h-4 lg:w-5 lg:h-5 inline mr-1.5 lg:mr-2" />
          {t('profitReport')}
        </button>
        <button
          onClick={() => setActiveTab('sales')}
          className={cn(
            'px-3 lg:px-6 py-2.5 lg:py-3 font-medium border-b-4 transition-colors whitespace-nowrap text-sm lg:text-base',
            activeTab === 'sales'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          )}
        >
          <DollarSign className="w-4 h-4 lg:w-5 lg:h-5 inline mr-1.5 lg:mr-2" />
          {t('salesReport')}
        </button>
        <button
          onClick={() => setActiveTab('sellers')}
          className={cn(
            'px-3 lg:px-6 py-2.5 lg:py-3 font-medium border-b-4 transition-colors whitespace-nowrap text-sm lg:text-base',
            activeTab === 'sellers'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          )}
        >
          <Users className="w-4 h-4 lg:w-5 lg:h-5 inline mr-1.5 lg:mr-2" />
          {t('sellerReport')}
        </button>
        <button
          onClick={() => setActiveTab('export')}
          className={cn(
            'px-3 lg:px-6 py-2.5 lg:py-3 font-medium border-b-4 transition-colors whitespace-nowrap text-sm lg:text-base',
            activeTab === 'export'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          )}
        >
          <Download className="w-4 h-4 lg:w-5 lg:h-5 inline mr-1.5 lg:mr-2" />
          {t('export')}
        </button>
      </div>

      {/* Profit Tab */}
      {activeTab === 'profit' && (
        <div className="space-y-4 lg:space-y-6">
          {loadingProfit ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : profitData ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 lg:gap-4">
                <Card>
                  <CardContent className="p-3 lg:p-6">
                    <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs lg:text-sm text-text-secondary">{t('totalRevenue')}</p>
                        <p className="text-sm lg:text-pos-xl font-bold text-primary truncate">
                          {formatMoney(profitData.summary.total_revenue)}
                        </p>
                      </div>
                      <DollarSign className="w-6 h-6 lg:w-10 lg:h-10 text-primary/20 hidden lg:block" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-3 lg:p-6">
                    <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs lg:text-sm text-text-secondary">{t('totalCostPrice')}</p>
                        <p className="text-sm lg:text-pos-xl font-bold text-warning truncate">
                          {formatMoney(profitData.summary.total_cost)}
                        </p>
                      </div>
                      <Package className="w-6 h-6 lg:w-10 lg:h-10 text-warning/20 hidden lg:block" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-3 lg:p-6">
                    <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs lg:text-sm text-text-secondary">{t('profit')}</p>
                        <p className={cn(
                          "text-sm lg:text-pos-xl font-bold truncate",
                          profitData.summary.total_profit >= 0 ? "text-success" : "text-danger"
                        )}>
                          {formatMoney(profitData.summary.total_profit)}
                        </p>
                      </div>
                      <TrendingUp className="w-6 h-6 lg:w-10 lg:h-10 text-success/20 hidden lg:block" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-3 lg:p-6">
                    <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs lg:text-sm text-text-secondary">{t('profitPercent')}</p>
                        <p className={cn(
                          "text-sm lg:text-pos-xl font-bold",
                          profitData.summary.profit_margin >= 0 ? "text-success" : "text-danger"
                        )}>
                          {profitData.summary.profit_margin.toFixed(1)}%
                        </p>
                      </div>
                      <div className="text-lg lg:text-2xl hidden lg:block">📊</div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Products Table */}
              <Card>
                <CardContent className="p-0">
                  <div className="p-3 lg:p-4 border-b border-border">
                    <h3 className="text-base lg:text-pos-lg font-bold">{t('profitByProducts')}</h3>
                    <p className="text-xs lg:text-sm text-text-secondary">
                      {profitData.summary.products_count} {t('product')}
                    </p>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[600px]">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-semibold">{t('product')}</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold">{t('quantity')}</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold">{t('costPrice')}</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold">{t('totalRevenue')}</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold">{t('profit')}</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold">%</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {profitData.data.map((item: any, index: number) => (
                          <tr key={item.product_id} className="hover:bg-gray-50">
                            <td className="px-4 py-3">
                              <div>
                                <p className="font-medium">{item.product_name}</p>
                                {item.product_article && (
                                  <p className="text-sm text-text-secondary">{item.product_article}</p>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right">{formatNumber(item.total_quantity)}</td>
                            <td className="px-4 py-3 text-right text-warning">
                              {formatMoney(item.total_cost)}
                            </td>
                            <td className="px-4 py-3 text-right">
                              {formatMoney(item.total_revenue)}
                            </td>
                            <td className={cn(
                              "px-4 py-3 text-right font-semibold",
                              item.total_profit >= 0 ? "text-success" : "text-danger"
                            )}>
                              {formatMoney(item.total_profit)}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <Badge variant={item.profit_margin >= 20 ? "success" : item.profit_margin >= 10 ? "warning" : "danger"}>
                                {item.profit_margin.toFixed(1)}%
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <p className="text-center py-12 text-text-secondary">{t('noData')}</p>
          )}
        </div>
      )}

      {/* Sales Tab */}
      {activeTab === 'sales' && (
        <div className="space-y-6">
          {loadingSales ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : salesData ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-text-secondary">{t('salesCount')}</p>
                    <p className="text-pos-xl font-bold">{salesData.summary.total_sales}</p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-text-secondary">{t('totalSum')}</p>
                    <p className="text-pos-lg font-bold text-primary">
                      {formatMoney(salesData.summary.total_amount)}
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-text-secondary">{t('discounts')}</p>
                    <p className="text-pos-lg font-bold text-warning">
                      {formatMoney(salesData.summary.total_discount)}
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-text-secondary">{t('paid')}</p>
                    <p className="text-pos-lg font-bold text-success">
                      {formatMoney(salesData.summary.total_paid)}
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-text-secondary">{t('debt')}</p>
                    <p className="text-pos-lg font-bold text-danger">
                      {formatMoney(salesData.summary.total_debt)}
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-text-secondary">{t('averageCheck')}</p>
                    <p className="text-pos-lg font-bold">
                      {formatMoney(salesData.summary.average_sale)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Payment Breakdown */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-pos-lg font-bold mb-4">{t('paymentType')}</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(salesData.payment_breakdown).map(([type, amount]: [string, any]) => (
                      <div key={type} className="p-4 bg-gray-50 rounded-pos">
                        <p className="text-sm text-text-secondary capitalize">{type}</p>
                        <p className="text-pos-lg font-bold">{formatMoney(amount)}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <p className="text-center py-12 text-text-secondary">{t('noData')}</p>
          )}
        </div>
      )}

      {/* Sellers/Kassirlar Tab */}
      {activeTab === 'sellers' && (
        <div className="space-y-4 lg:space-y-6">
          {/* Seller selector */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-600 mb-2">{t('selectSeller')}</label>
                  <select
                    value={selectedSellerId}
                    onChange={(e) => setSelectedSellerId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full h-12 px-4 border-2 border-gray-200 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">{t('all')} {t('sellersList').toLowerCase()}</option>
                    {sellersSummary?.sellers?.map((seller: any) => (
                      <option key={seller.id} value={seller.id}>
                        {seller.name} ({seller.sales_count} - {formatMoney(seller.total_amount)})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* All Sellers Summary */}
          {!selectedSellerId && (
            <>
              {loadingSellersSummary ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : sellersSummary ? (
                <>
                  {/* Totals Summary */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <Card className="bg-blue-50">
                      <CardContent className="p-4">
                        <p className="text-xs text-blue-600">{t('totalSales')}</p>
                        <p className="text-xl font-bold text-blue-700">{sellersSummary.totals.total_sales}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-green-50">
                      <CardContent className="p-4">
                        <p className="text-xs text-green-600">{t('totalSum')}</p>
                        <p className="text-xl font-bold text-green-700">{formatMoney(sellersSummary.totals.total_amount)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-purple-50">
                      <CardContent className="p-4">
                        <p className="text-xs text-purple-600">{t('paid')}</p>
                        <p className="text-xl font-bold text-purple-700">{formatMoney(sellersSummary.totals.total_paid)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-red-50">
                      <CardContent className="p-4">
                        <p className="text-xs text-red-600">{t('onCredit')}</p>
                        <p className="text-xl font-bold text-red-700">{formatMoney(sellersSummary.totals.total_debt)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Sellers List */}
                  <Card>
                    <CardContent className="p-4">
                      <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                        <Users className="w-5 h-5" />
                        {t('sellersList')}
                      </h3>
                      <div className="space-y-3">
                        {sellersSummary.sellers?.map((seller: any) => (
                          <div
                            key={seller.id}
                            onClick={() => setSelectedSellerId(seller.id)}
                            className="p-4 border-2 rounded-xl cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                                  <User className="w-6 h-6 text-blue-600" />
                                </div>
                                <div>
                                  <p className="font-semibold text-base">{seller.name}</p>
                                  <p className="text-sm text-gray-500">@{seller.username}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-lg text-green-600">{formatMoney(seller.total_amount)}</p>
                                <p className="text-sm text-gray-500">{seller.sales_count} {t('sales').toLowerCase()}</p>
                              </div>
                            </div>
                            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                              <div className="bg-green-50 rounded-lg p-2">
                                <p className="text-xs text-green-600">{t('paid')}</p>
                                <p className="font-semibold text-green-700 text-sm">{formatMoney(seller.total_paid)}</p>
                              </div>
                              <div className="bg-red-50 rounded-lg p-2">
                                <p className="text-xs text-red-600">{t('onCredit')}</p>
                                <p className="font-semibold text-red-700 text-sm">{formatMoney(seller.total_debt)}</p>
                              </div>
                              <div className="bg-blue-50 rounded-lg p-2">
                                <p className="text-xs text-blue-600">{t('averageCheck')}</p>
                                <p className="font-semibold text-blue-700 text-sm">
                                  {formatMoney(seller.sales_count > 0 ? seller.total_amount / seller.sales_count : 0)}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : null}
            </>
          )}

          {/* Selected Seller Stats */}
          {selectedSellerId && (
            <>
              {loadingSellerStats ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : sellerStats ? (
                <>
                  {/* Seller Info */}
                  <Card className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                            <User className="w-8 h-8" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold">{sellerStats.seller.name}</h2>
                            <p className="text-blue-100">@{sellerStats.seller.username} • {sellerStats.seller.role}</p>
                          </div>
                        </div>
                        <Button
                          onClick={async () => {
                            try {
                              toast.loading(t('excelPreparing'))
                              const response = await api.get('/reports/excel/seller-stats', {
                                params: { seller_id: selectedSellerId, start_date: startDate, end_date: endDate },
                                responseType: 'blob'
                              })
                              const url = window.URL.createObjectURL(new Blob([response.data]))
                              const link = document.createElement('a')
                              link.href = url
                              link.setAttribute('download', `kassir_${sellerStats.seller.username}_${startDate}_${endDate}.xlsx`)
                              document.body.appendChild(link)
                              link.click()
                              link.remove()
                              toast.dismiss()
                              toast.success(t('excelDownloaded'))
                            } catch (error) {
                              toast.dismiss()
                              toast.error(t('excelError'))
                            }
                          }}
                          className="bg-white/20 hover:bg-white/30 text-white border-0"
                        >
                          <Download className="w-5 h-5 mr-2" />
                          {t('downloadExcel2')}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <ShoppingCart className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">{t('salesCount')}</p>
                            <p className="text-xl font-bold">{sellerStats.summary.total_sales_count}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-green-100 rounded-lg">
                            <DollarSign className="w-5 h-5 text-green-600" />
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">{t('totalSum')}</p>
                            <p className="text-xl font-bold text-green-600">{formatMoney(sellerStats.summary.total_amount)}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-purple-100 rounded-lg">
                            <CreditCard className="w-5 h-5 text-purple-600" />
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">{t('paid')}</p>
                            <p className="text-xl font-bold text-purple-600">{formatMoney(sellerStats.summary.total_paid)}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-red-100 rounded-lg">
                            <Banknote className="w-5 h-5 text-red-600" />
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">{t('soldOnCredit')}</p>
                            <p className="text-xl font-bold text-red-600">{formatMoney(sellerStats.summary.total_debt)}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Additional Stats */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <Card className="bg-yellow-50">
                      <CardContent className="p-3">
                        <p className="text-xs text-yellow-600">{t('averageCheck')}</p>
                        <p className="text-lg font-bold text-yellow-700">{formatMoney(sellerStats.summary.average_sale)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-indigo-50">
                      <CardContent className="p-3">
                        <p className="text-xs text-indigo-600">{t('customersCount')}</p>
                        <p className="text-lg font-bold text-indigo-700">{sellerStats.summary.unique_customers}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-gray-50">
                      <CardContent className="p-3">
                        <p className="text-xs text-gray-600">{t('anonymousSales')}</p>
                        <p className="text-lg font-bold text-gray-700">{sellerStats.summary.anonymous_sales}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-orange-50">
                      <CardContent className="p-3">
                        <p className="text-xs text-orange-600">{t('discounts')}</p>
                        <p className="text-lg font-bold text-orange-700">{formatMoney(sellerStats.summary.total_discount)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Payment Breakdown */}
                  <Card>
                    <CardContent className="p-4">
                      <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                        <CreditCard className="w-5 h-5" />
                        {t('paymentType')}
                      </h3>
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        <div className="bg-green-50 rounded-xl p-4 text-center">
                          <Banknote className="w-8 h-8 text-green-600 mx-auto mb-2" />
                          <p className="text-xs text-green-600">{t('cash')}</p>
                          <p className="text-lg font-bold text-green-700">{formatMoney(sellerStats.payment_breakdown.CASH || 0)}</p>
                        </div>
                        <div className="bg-blue-50 rounded-xl p-4 text-center">
                          <CreditCard className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                          <p className="text-xs text-blue-600">{t('card')}</p>
                          <p className="text-lg font-bold text-blue-700">{formatMoney(sellerStats.payment_breakdown.CARD || 0)}</p>
                        </div>
                        <div className="bg-purple-50 rounded-xl p-4 text-center">
                          <Building className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                          <p className="text-xs text-purple-600">{t('transfer')}</p>
                          <p className="text-lg font-bold text-purple-700">{formatMoney(sellerStats.payment_breakdown.TRANSFER || 0)}</p>
                        </div>
                        <div className="bg-red-50 rounded-xl p-4 text-center">
                          <Package className="w-8 h-8 text-red-600 mx-auto mb-2" />
                          <p className="text-xs text-red-600">{t('debt')}</p>
                          <p className="text-lg font-bold text-red-700">{formatMoney(sellerStats.summary.total_debt)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Collapsible Sections */}
                  {/* Daily Breakdown */}
                  <Card>
                    <CardContent className="p-4">
                      <button
                        onClick={() => setExpandedSection(expandedSection === 'daily' ? null : 'daily')}
                        className="w-full flex items-center justify-between"
                      >
                        <h3 className="font-bold text-lg flex items-center gap-2">
                          <Calendar className="w-5 h-5" />
                          {t('dailyIndicators')}
                        </h3>
                        {expandedSection === 'daily' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                      {expandedSection === 'daily' && (
                        <div className="mt-4 space-y-2 max-h-80 overflow-y-auto">
                          {sellerStats.daily_breakdown?.map((day: any) => (
                            <div key={day.date} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div>
                                <p className="font-medium">{formatDateTashkent(day.date)}</p>
                                <p className="text-sm text-gray-500">{day.sales_count} {t('sales').toLowerCase()}</p>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-green-600">{formatMoney(day.total_amount)}</p>
                                {day.debt_amount > 0 && (
                                  <p className="text-sm text-red-500">{t('debt')}: {formatMoney(day.debt_amount)}</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Customers */}
                  <Card>
                    <CardContent className="p-4">
                      <button
                        onClick={() => setExpandedSection(expandedSection === 'customers' ? null : 'customers')}
                        className="w-full flex items-center justify-between"
                      >
                        <h3 className="font-bold text-lg flex items-center gap-2">
                          <Users className="w-5 h-5" />
                          {t('customers')} ({sellerStats.customers?.length || 0})
                        </h3>
                        {expandedSection === 'customers' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                      {expandedSection === 'customers' && (
                        <div className="mt-4 space-y-2 max-h-80 overflow-y-auto">
                          {sellerStats.customers?.map((cust: any) => (
                            <div key={cust.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-center gap-3">
                                <div className={cn(
                                  "w-10 h-10 rounded-full flex items-center justify-center",
                                  cust.customer_type === 'VIP' ? "bg-yellow-100" : "bg-blue-100"
                                )}>
                                  <User className={cn(
                                    "w-5 h-5",
                                    cust.customer_type === 'VIP' ? "text-yellow-600" : "text-blue-600"
                                  )} />
                                </div>
                                <div>
                                  <p className="font-medium">{cust.name}</p>
                                  <p className="text-sm text-gray-500 flex items-center gap-1">
                                    <Phone className="w-3 h-3" />
                                    {cust.phone}
                                  </p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-green-600">{formatMoney(cust.total_amount)}</p>
                                <p className="text-sm text-gray-500">{cust.sales_count} {t('purchase')}</p>
                                {cust.total_debt > 0 && (
                                  <p className="text-xs text-red-500">{t('debt')}: {formatMoney(cust.total_debt)}</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Top Products */}
                  <Card>
                    <CardContent className="p-4">
                      <button
                        onClick={() => setExpandedSection(expandedSection === 'products' ? null : 'products')}
                        className="w-full flex items-center justify-between"
                      >
                        <h3 className="font-bold text-lg flex items-center gap-2">
                          <Package className="w-5 h-5" />
                          {t('topProducts')} ({sellerStats.top_products?.length || 0})
                        </h3>
                        {expandedSection === 'products' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                      {expandedSection === 'products' && (
                        <div className="mt-4 space-y-2 max-h-80 overflow-y-auto">
                          {sellerStats.top_products?.map((prod: any, idx: number) => (
                            <div key={prod.product_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-bold text-blue-600">
                                  {idx + 1}
                                </div>
                                <div>
                                  <p className="font-medium">{prod.product_name}</p>
                                  <p className="text-sm text-gray-500">{prod.times_sold} {t('timesSold')}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-green-600">{formatMoney(prod.total_revenue)}</p>
                                <p className="text-sm text-gray-500">{formatNumber(prod.total_quantity)} {t('pieces')}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Recent Sales */}
                  <Card>
                    <CardContent className="p-4">
                      <button
                        onClick={() => setExpandedSection(expandedSection === 'sales' ? null : 'sales')}
                        className="w-full flex items-center justify-between"
                      >
                        <h3 className="font-bold text-lg flex items-center gap-2">
                          <ShoppingCart className="w-5 h-5" />
                          {t('recentSalesTitle')} ({sellerStats.recent_sales?.length || 0})
                        </h3>
                        {expandedSection === 'sales' ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                      {expandedSection === 'sales' && (
                        <div className="mt-4 space-y-2 max-h-96 overflow-y-auto">
                          {sellerStats.recent_sales?.map((sale: any) => (
                            <div key={sale.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div>
                                <p className="font-medium">#{sale.sale_number}</p>
                                <p className="text-sm text-gray-600">{sale.customer_name}</p>
                                <p className="text-xs text-gray-400">
                                  {formatDateTimeTashkent(sale.created_at)}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-green-600">{formatMoney(sale.total_amount)}</p>
                                <p className="text-sm text-gray-500">{sale.items_count} {t('product')}</p>
                                {sale.debt_amount > 0 && (
                                  <Badge variant="danger" className="text-xs mt-1">{t('debt')}: {formatMoney(sale.debt_amount)}</Badge>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </>
              ) : null}
            </>
          )}
        </div>
      )}

      {/* Export Tab */}
      {activeTab === 'export' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Sales Report */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-primary/10 rounded-pos">
                  <DollarSign className="w-8 h-8 text-primary" />
                </div>
                <div>
                  <h3 className="font-bold text-pos-lg">{t('salesReportTitle')}</h3>
                  <p className="text-sm text-text-secondary">{t('forSelectedPeriod')}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadExcel('sales')}
                >
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Excel
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadPDF('sales')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  PDF
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Stock Report */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-warning/10 rounded-pos">
                  <Package className="w-8 h-8 text-warning" />
                </div>
                <div>
                  <h3 className="font-bold text-pos-lg">{t('stockReportTitle')}</h3>
                  <p className="text-sm text-text-secondary">{t('currentStatus')}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadExcel('stock')}
                >
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Excel
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadPDF('stock')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  PDF
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Debtors Report */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-danger/10 rounded-pos">
                  <Users className="w-8 h-8 text-danger" />
                </div>
                <div>
                  <h3 className="font-bold text-pos-lg">{t('debtorsReportTitle')}</h3>
                  <p className="text-sm text-text-secondary">{t('currentDebts')}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadExcel('debtors')}
                >
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Excel
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadPDF('debtors')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  PDF
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Daily Report */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-success/10 rounded-pos">
                  <Calendar className="w-8 h-8 text-success" />
                </div>
                <div>
                  <h3 className="font-bold text-pos-lg">{t('dailyReportTitle')}</h3>
                  <p className="text-sm text-text-secondary">{t('forToday')}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadExcel('daily')}
                >
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Excel
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadPDF('daily')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  PDF
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Price List */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-primary/10 rounded-pos">
                  <FileSpreadsheet className="w-8 h-8 text-primary" />
                </div>
                <div>
                  <h3 className="font-bold text-pos-lg">{t('priceListTitle')}</h3>
                  <p className="text-sm text-text-secondary">{t('allProducts')}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadExcel('price-list')}
                >
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Excel
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => handleDownloadPDF('price-list')}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  PDF
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
