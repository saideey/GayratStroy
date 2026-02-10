import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { 
  Search, Plus, Phone, CreditCard, User, Banknote, Calendar,
  ShoppingCart, Eye, Loader2, Building, Mail, MapPin, ChevronDown, ChevronRight, Download, Package, Edit, Trash2, AlertTriangle, Users, FileSpreadsheet
} from 'lucide-react'
import toast from 'react-hot-toast'
import { 
  Button, Input, Card, CardContent, Badge,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription 
} from '@/components/ui'
import { customersService } from '@/services'
import api from '@/services/api'
import { formatMoney, formatPhone, formatInputNumber, cn, formatDateTashkent, formatTimeTashkent, formatDateTimeTashkent } from '@/lib/utils'
import { useLanguage } from '@/contexts/LanguageContext'
import type { Customer, Sale, User as UserType } from '@/types'

interface CustomerFormData {
  name: string
  phone: string
  phone_secondary?: string
  telegram_id?: string
  company_name?: string
  email?: string
  address?: string
  customer_type: 'REGULAR' | 'VIP' | 'WHOLESALE'
  credit_limit?: number
  manager_id?: number  // Biriktirilgan kassir
}

interface PaymentFormData {
  amount: number
  payment_type: string
  description?: string
}

interface SaleItem {
  id: number
  product_name: string
  quantity: number
  uom_symbol: string
  unit_price: number
  total_price: number
  discount_amount: number
}

interface DebtRecord {
  id: number
  transaction_type: string
  amount: number
  balance_before: number
  balance_after: number
  reference_type: string
  description: string
  created_at: string
}

export default function CustomersPage() {
  const queryClient = useQueryClient()
  const { t } = useLanguage()
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<string>('')
  const [filterSellerId, setFilterSellerId] = useState<number | ''>('')
  const [showDebtorsOnly, setShowDebtorsOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showPaymentDialog, setShowPaymentDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [expandedSaleId, setExpandedSaleId] = useState<number | null>(null)
  const [saleItems, setSaleItems] = useState<Record<number, SaleItem[]>>({})
  const [loadingSaleItems, setLoadingSaleItems] = useState<number | null>(null)
  const [paymentAmountDisplay, setPaymentAmountDisplay] = useState('')

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<CustomerFormData>({
    defaultValues: { customer_type: 'REGULAR', credit_limit: 0 }
  })

  const { register: registerPayment, handleSubmit: handlePaymentSubmit, reset: resetPayment, setValue: setPaymentValue } = useForm<PaymentFormData>({
    defaultValues: { payment_type: 'CASH' }
  })

  // Fetch customers
  const { data: customersData, isLoading } = useQuery({
    queryKey: ['customers', searchQuery, filterType, filterSellerId, showDebtorsOnly, page],
    queryFn: () => customersService.getCustomers({
      q: searchQuery || undefined,
      customer_type: filterType || undefined,
      manager_id: filterSellerId || undefined,
      has_debt: showDebtorsOnly || undefined,
      page,
      per_page: 20,
    }),
  })

  // Fetch sellers (users who can be assigned to customers)
  const { data: sellersData } = useQuery({
    queryKey: ['sellers-list'],
    queryFn: async () => {
      const response = await api.get('/users?per_page=100')
      return response.data
    },
  })

  // Fetch debtors summary
  const { data: debtorsData } = useQuery({
    queryKey: ['debtors-summary'],
    queryFn: () => customersService.getDebtors(),
  })

  // Fetch customer sales
  const { data: customerSales, isLoading: loadingSales } = useQuery({
    queryKey: ['customer-sales', selectedCustomer?.id],
    queryFn: async () => {
      if (!selectedCustomer) return null
      const response = await api.get(`/sales?customer_id=${selectedCustomer.id}&per_page=100`)
      return response.data
    },
    enabled: !!selectedCustomer && showDetailDialog,
  })

  // Fetch customer debt history (with running balance)
  const { data: customerDebtHistory } = useQuery({
    queryKey: ['customer-debt-history', selectedCustomer?.id],
    queryFn: async () => {
      if (!selectedCustomer) return null
      const response = await api.get(`/customers/${selectedCustomer.id}/debt-history?per_page=100`)
      return response.data
    },
    enabled: !!selectedCustomer && showDetailDialog,
  })

  // Load sale items when expanding a row
  const loadSaleItems = async (saleId: number) => {
    if (saleItems[saleId]) {
      setExpandedSaleId(expandedSaleId === saleId ? null : saleId)
      return
    }
    
    setLoadingSaleItems(saleId)
    try {
      const response = await api.get(`/sales/${saleId}`)
      setSaleItems(prev => ({ ...prev, [saleId]: response.data.data.items }))
      setExpandedSaleId(saleId)
    } catch (error) {
      toast.error('Xatolik yuz berdi')
    } finally {
      setLoadingSaleItems(null)
    }
  }

  // Export ALL customer data to single professional Excel file
  const exportCustomerDataToExcel = async () => {
    if (!selectedCustomer) return
    
    try {
      toast.loading('Hisobot tayyorlanmoqda...')
      
      // Dynamic imports
      const ExcelJS = await import('exceljs')
      const { saveAs } = await import('file-saver')
      
      // Use already fetched data or fetch if not available
      let salesData = customerSales?.data || []
      let debtData = customerDebtHistory?.data || []
      
      // If data not available, fetch it
      if (salesData.length === 0) {
        try {
          const res = await api.get(`/customers/${selectedCustomer.id}/sales`)
          salesData = res.data?.data || []
        } catch (e) {
          console.log('Sales fetch failed', e)
        }
      }
      
      if (debtData.length === 0) {
        try {
          const res = await api.get(`/customers/${selectedCustomer.id}/debt-history`)
          debtData = res.data?.data || []
        } catch (e) {
          console.log('Debt fetch failed', e)
        }
      }
      
      // Fetch detailed items for each sale
      const salesWithItems = await Promise.all(
        salesData.map(async (sale: any) => {
          try {
            const response = await api.get(`/sales/${sale.id}`)
            return { ...sale, items: response.data?.data?.items || response.data?.items || [] }
          } catch {
            return { ...sale, items: [] }
          }
        })
      )
      
      // Create workbook
      const workbook = new ExcelJS.Workbook()
      workbook.creator = 'Gayrat Stroy House ERP'
      workbook.created = new Date()
      
      const ws = workbook.addWorksheet('Mijoz hisoboti', {
        pageSetup: { paperSize: 9, orientation: 'landscape' }
      })
      
      // Define colors
      const colors = {
        header: '1F4E79',      // Dark blue
        subHeader: '2E75B6',   // Medium blue
        tableHeader: '4472C4', // Light blue
        success: '70AD47',     // Green
        danger: 'C00000',      // Red
        warning: 'FFC000',     // Yellow/Orange
        lightBlue: 'D6DCE4',   // Light gray-blue
        lightGreen: 'E2EFDA',  // Light green
        lightRed: 'FCE4D6',    // Light red/peach
        white: 'FFFFFF',
        black: '000000',
        gray: '808080'
      }
      
      // Helper function for border style
      const thinBorder = {
        top: { style: 'thin' as const, color: { argb: 'FF000000' } },
        left: { style: 'thin' as const, color: { argb: 'FF000000' } },
        bottom: { style: 'thin' as const, color: { argb: 'FF000000' } },
        right: { style: 'thin' as const, color: { argb: 'FF000000' } }
      }
      
      let currentRow = 1
      
      // ═══════════════════════════════════════════════════════════════
      // SECTION 1: HEADER - Company and Report Title
      // ═══════════════════════════════════════════════════════════════
      ws.mergeCells(`A${currentRow}:K${currentRow}`)
      const titleCell = ws.getCell(`A${currentRow}`)
      titleCell.value = '🏢 Gayrat Stroy House - MIJOZ HISOBOTI'
      titleCell.font = { bold: true, size: 18, color: { argb: 'FF' + colors.white } }
      titleCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.header } }
      titleCell.alignment = { horizontal: 'center', vertical: 'middle' }
      ws.getRow(currentRow).height = 35
      currentRow += 2
      
      // ═══════════════════════════════════════════════════════════════
      // SECTION 2: CUSTOMER INFO
      // ═══════════════════════════════════════════════════════════════
      ws.mergeCells(`A${currentRow}:E${currentRow}`)
      const custHeader = ws.getCell(`A${currentRow}`)
      custHeader.value = '👤 MIJOZ MA\'LUMOTLARI'
      custHeader.font = { bold: true, size: 12, color: { argb: 'FF' + colors.white } }
      custHeader.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.subHeader } }
      custHeader.alignment = { horizontal: 'center' }
      
      ws.mergeCells(`F${currentRow}:K${currentRow}`)
      const statsHeader = ws.getCell(`F${currentRow}`)
      statsHeader.value = '📊 MOLIYAVIY STATISTIKA'
      statsHeader.font = { bold: true, size: 12, color: { argb: 'FF' + colors.white } }
      statsHeader.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.success } }
      statsHeader.alignment = { horizontal: 'center' }
      currentRow++
      
      // Calculate statistics
      const totalSalesCount = salesData.length
      const totalAmount = salesData.reduce((sum: number, s: any) => sum + Number(s.total_amount || 0), 0)
      const totalPaid = salesData.reduce((sum: number, s: any) => sum + Number(s.paid_amount || 0), 0)
      const totalDebtFromSales = salesData.reduce((sum: number, s: any) => sum + Number(s.debt_amount || 0), 0)
      const totalPayments = debtData
        .filter((r: any) => r.transaction_type === 'PAYMENT' || r.transaction_type === 'DEBT_PAYMENT')
        .reduce((sum: number, r: any) => sum + Math.abs(Number(r.amount || 0)), 0)
      const totalItemsCount = salesWithItems.reduce((sum: number, s: any) => sum + (s.items?.length || 0), 0)
      
      // Customer info rows
      const customerInfo = [
        ['Mijoz ismi:', selectedCustomer.name, '', '', '', 'Jami xaridlar:', `${totalSalesCount} ta`],
        ['Telefon:', selectedCustomer.phone, '', '', '', 'Jami summa:', formatMoney(totalAmount)],
        ['Telegram:', selectedCustomer.telegram_id || '-', '', '', '', 'To\'langan:', formatMoney(totalPaid)],
        ['Kompaniya:', selectedCustomer.company_name || '-', '', '', '', 'Qarz (sotuvlardan):', formatMoney(totalDebtFromSales)],
        ['Manzil:', selectedCustomer.address || '-', '', '', '', 'To\'lovlar (alohida):', formatMoney(totalPayments)],
        ['Mijoz turi:', selectedCustomer.customer_type === 'VIP' ? '⭐ VIP Mijoz' : 'Oddiy mijoz', '', '', '', 'Sotib olingan tovarlar:', `${totalItemsCount} ta`],
      ]
      
      customerInfo.forEach((row) => {
        const r = ws.addRow(row)
        r.getCell(1).font = { bold: true, color: { argb: 'FF' + colors.subHeader } }
        r.getCell(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.lightBlue } }
        r.getCell(2).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.white } }
        r.getCell(6).font = { bold: true, color: { argb: 'FF' + colors.success } }
        r.getCell(6).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.lightGreen } }
        r.getCell(7).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.white } }
        r.getCell(7).alignment = { horizontal: 'right' }
        currentRow++
      })
      
      // Current debt highlight
      currentRow++
      ws.mergeCells(`A${currentRow}:C${currentRow}`)
      const debtLabelCell = ws.getCell(`A${currentRow}`)
      debtLabelCell.value = '💰 JORIY QARZ:'
      debtLabelCell.font = { bold: true, size: 14, color: { argb: 'FF' + colors.white } }
      debtLabelCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + (selectedCustomer.current_debt > 0 ? colors.danger : colors.success) } }
      debtLabelCell.alignment = { horizontal: 'center', vertical: 'middle' }
      
      ws.mergeCells(`D${currentRow}:F${currentRow}`)
      const debtValueCell = ws.getCell(`D${currentRow}`)
      debtValueCell.value = formatMoney(selectedCustomer.current_debt)
      debtValueCell.font = { bold: true, size: 14, color: { argb: 'FF' + (selectedCustomer.current_debt > 0 ? colors.danger : colors.success) } }
      debtValueCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + (selectedCustomer.current_debt > 0 ? colors.lightRed : colors.lightGreen) } }
      debtValueCell.alignment = { horizontal: 'center', vertical: 'middle' }
      
      ws.mergeCells(`G${currentRow}:K${currentRow}`)
      const dateCell = ws.getCell(`G${currentRow}`)
      dateCell.value = `📅 Hisobot sanasi: ${formatDateTimeTashkent(new Date())}`
      dateCell.font = { italic: true, color: { argb: 'FF' + colors.gray } }
      dateCell.alignment = { horizontal: 'right' }
      
      ws.getRow(currentRow).height = 25
      currentRow += 2
      
      // ═══════════════════════════════════════════════════════════════
      // SECTION 3: SALES HISTORY TABLE
      // ═══════════════════════════════════════════════════════════════
      ws.mergeCells(`A${currentRow}:K${currentRow}`)
      const salesTitle = ws.getCell(`A${currentRow}`)
      salesTitle.value = `🛒 SOTUVLAR TARIXI (${totalSalesCount} ta xarid)`
      salesTitle.font = { bold: true, size: 12, color: { argb: 'FF' + colors.white } }
      salesTitle.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.tableHeader } }
      salesTitle.alignment = { horizontal: 'center' }
      ws.getRow(currentRow).height = 22
      currentRow++
      
      // Sales table header
      const salesHeaders = ['№', 'Sana', 'Vaqt', 'Chek raqami', 'Tovarlar soni', 'Umumiy summa', 'To\'langan', 'Qarz', 'Holat', '', '']
      const salesHeaderRow = ws.addRow(salesHeaders)
      salesHeaderRow.eachCell((cell, colNumber) => {
        if (colNumber <= 9) {
          cell.font = { bold: true, color: { argb: 'FF' + colors.white } }
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.subHeader } }
          cell.alignment = { horizontal: 'center', vertical: 'middle' }
          cell.border = thinBorder
        }
      })
      ws.getRow(currentRow).height = 20
      currentRow++
      
      // Sales data rows
      if (salesWithItems.length > 0) {
        salesWithItems.forEach((sale: any, index: number) => {
          const status = sale.payment_status === 'PAID' ? '✅ To\'langan' :
                        sale.payment_status === 'DEBT' ? '❌ Qarzga' :
                        sale.payment_status === 'PARTIAL' ? '⚠️ Qisman' : sale.payment_status
          
          const rowData = [
            index + 1,
            formatDateTashkent(sale.created_at),
            formatTimeTashkent(sale.created_at),
            sale.sale_number || '-',
            `${sale.items?.length || sale.items_count || 0} ta`,
            Number(sale.total_amount || 0),
            Number(sale.paid_amount || 0),
            Number(sale.debt_amount || 0),
            status,
            '',
            ''
          ]
          
          const dataRow = ws.addRow(rowData)
          dataRow.eachCell((cell, colNumber) => {
            if (colNumber <= 9) {
              cell.border = thinBorder
              cell.alignment = { horizontal: colNumber <= 5 ? 'center' : 'right', vertical: 'middle' }
              
              // Alternate row colors
              if (index % 2 === 0) {
                cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.lightBlue } }
              }
              
              // Format numbers
              if (colNumber >= 6 && colNumber <= 8) {
                cell.numFmt = '#,##0'
              }
              
              // Color status
              if (colNumber === 9) {
                cell.alignment = { horizontal: 'center' }
                if (sale.payment_status === 'PAID') {
                  cell.font = { color: { argb: 'FF' + colors.success } }
                } else if (sale.payment_status === 'DEBT') {
                  cell.font = { color: { argb: 'FF' + colors.danger } }
                } else {
                  cell.font = { color: { argb: 'FF' + colors.warning } }
                }
              }
            }
          })
          currentRow++
        })
        
        // Sales totals row
        const salesTotalRow = ws.addRow(['', '', '', '', 'JAMI:', totalAmount, totalPaid, totalDebtFromSales, '', '', ''])
        salesTotalRow.eachCell((cell, colNumber) => {
          if (colNumber >= 5 && colNumber <= 8) {
            cell.font = { bold: true }
            cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.warning } }
            cell.border = thinBorder
            if (colNumber >= 6) {
              cell.numFmt = '#,##0'
              cell.alignment = { horizontal: 'right' }
            }
          }
        })
        currentRow++
      } else {
        const noDataRow = ws.addRow(['', '', '', '', 'Ma\'lumot yo\'q', '', '', '', '', '', ''])
        noDataRow.getCell(5).font = { italic: true, color: { argb: 'FF' + colors.gray } }
        currentRow++
      }
      
      currentRow++
      
      // ═══════════════════════════════════════════════════════════════
      // SECTION 4: DETAILED ITEMS TABLE
      // ═══════════════════════════════════════════════════════════════
      ws.mergeCells(`A${currentRow}:K${currentRow}`)
      const itemsTitle = ws.getCell(`A${currentRow}`)
      itemsTitle.value = `📦 SOTIB OLINGAN TOVARLAR BATAFSIL (${totalItemsCount} ta tovar)`
      itemsTitle.font = { bold: true, size: 12, color: { argb: 'FF' + colors.white } }
      itemsTitle.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.success } }
      itemsTitle.alignment = { horizontal: 'center' }
      ws.getRow(currentRow).height = 22
      currentRow++
      
      // Items table header
      const itemsHeaders = ['№', 'Sana', 'Chek №', 'Tovar nomi', 'Artikul', 'Miqdor', 'O\'lchov', 'Narx', 'Chegirma', 'Summa', '']
      const itemsHeaderRow = ws.addRow(itemsHeaders)
      itemsHeaderRow.eachCell((cell, colNumber) => {
        if (colNumber <= 10) {
          cell.font = { bold: true, color: { argb: 'FF' + colors.white } }
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF70AD47' } }
          cell.alignment = { horizontal: 'center', vertical: 'middle' }
          cell.border = thinBorder
        }
      })
      ws.getRow(currentRow).height = 20
      currentRow++
      
      // Items data
      let itemNo = 0
      let totalItemsSum = 0
      
      if (salesWithItems.length > 0) {
        salesWithItems.forEach((sale: any) => {
          if (sale.items && sale.items.length > 0) {
            sale.items.forEach((item: any) => {
              itemNo++
              const itemSum = Number(item.total || item.total_price || (item.quantity * (item.unit_price || item.price || 0)) || 0)
              totalItemsSum += itemSum
              
              const itemRowData = [
                itemNo,
                formatDateTashkent(sale.created_at),
                sale.sale_number || '-',
                item.product_name || item.name || '-',
                item.product_article || item.article || '-',
                Number(item.quantity || 0),
                item.uom_symbol || item.uom || '-',
                Number(item.unit_price || item.price || 0),
                Number(item.discount || 0),
                itemSum,
                ''
              ]
              
              const itemRow = ws.addRow(itemRowData)
              itemRow.eachCell((cell, colNumber) => {
                if (colNumber <= 10) {
                  cell.border = thinBorder
                  cell.alignment = { horizontal: colNumber <= 5 ? 'left' : (colNumber <= 7 ? 'center' : 'right'), vertical: 'middle' }
                  
                  if (itemNo % 2 === 0) {
                    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.lightGreen } }
                  }
                  
                  if (colNumber >= 6 && colNumber !== 7) {
                    cell.numFmt = '#,##0'
                  }
                }
              })
              currentRow++
            })
          }
        })
        
        // Items total row
        if (totalItemsCount > 0) {
          const itemsTotalRow = ws.addRow(['', '', '', '', '', '', '', '', 'JAMI:', totalItemsSum, ''])
          itemsTotalRow.eachCell((cell, colNumber) => {
            if (colNumber >= 9 && colNumber <= 10) {
              cell.font = { bold: true }
              cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.success } }
              cell.border = thinBorder
              if (colNumber === 10) {
                cell.numFmt = '#,##0'
                cell.alignment = { horizontal: 'right' }
              }
            }
          })
          currentRow++
        }
      } else {
        const noItemsRow = ws.addRow(['', '', '', 'Tovarlar ma\'lumoti yo\'q', '', '', '', '', '', '', ''])
        noItemsRow.getCell(4).font = { italic: true, color: { argb: 'FF' + colors.gray } }
        currentRow++
      }
      
      currentRow++
      
      // ═══════════════════════════════════════════════════════════════
      // SECTION 5: DEBT & PAYMENTS HISTORY
      // ═══════════════════════════════════════════════════════════════
      ws.mergeCells(`A${currentRow}:K${currentRow}`)
      const debtTitle = ws.getCell(`A${currentRow}`)
      debtTitle.value = `💳 QARZ VA TO'LOVLAR TARIXI (${debtData.length} ta yozuv)`
      debtTitle.font = { bold: true, size: 12, color: { argb: 'FF' + colors.white } }
      debtTitle.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.danger } }
      debtTitle.alignment = { horizontal: 'center' }
      ws.getRow(currentRow).height = 22
      currentRow++
      
      // Debt table header
      const debtHeaders = ['№', 'Sana', 'Vaqt', 'Turi', 'Summa', 'Qarz oldin', 'Qarz keyin', 'O\'zgarish', '', 'Izoh', '']
      const debtHeaderRow = ws.addRow(debtHeaders)
      debtHeaderRow.eachCell((cell, colNumber) => {
        if (colNumber <= 8 || colNumber === 10) {
          cell.font = { bold: true, color: { argb: 'FF' + colors.white } }
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFC00000' } }
          cell.alignment = { horizontal: 'center', vertical: 'middle' }
          cell.border = thinBorder
        }
      })
      ws.getRow(currentRow).height = 20
      currentRow++
      
      // Debt data
      if (debtData.length > 0) {
        debtData.forEach((record: any, index: number) => {
          const isPayment = record.transaction_type === 'PAYMENT' || record.transaction_type === 'DEBT_PAYMENT'
          const typeLabel = isPayment ? '💰 To\'lov' : '📦 Xarid'
          const change = Number(record.balance_after || 0) - Number(record.balance_before || 0)
          
          const debtRowData = [
            index + 1,
            formatDateTashkent(record.created_at),
            formatTimeTashkent(record.created_at),
            typeLabel,
            Math.abs(Number(record.amount || 0)),
            Number(record.balance_before || 0),
            Number(record.balance_after || 0),
            change,
            '',
            record.description || '-',
            ''
          ]
          
          const debtRow = ws.addRow(debtRowData)
          debtRow.eachCell((cell, colNumber) => {
            if (colNumber <= 8 || colNumber === 10) {
              cell.border = thinBorder
              cell.alignment = { horizontal: colNumber <= 4 || colNumber === 10 ? 'left' : 'right', vertical: 'middle' }
              
              // Alternate colors based on type
              if (isPayment) {
                cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.lightGreen } }
              } else {
                cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + colors.lightRed } }
              }
              
              if (colNumber >= 5 && colNumber <= 8) {
                cell.numFmt = '#,##0'
              }
              
              // Color change column
              if (colNumber === 8) {
                cell.font = { bold: true, color: { argb: 'FF' + (change < 0 ? colors.success : colors.danger) } }
              }
            }
          })
          currentRow++
        })
      } else {
        const noDebtRow = ws.addRow(['', '', '', 'Ma\'lumot yo\'q', '', '', '', '', '', '', ''])
        noDebtRow.getCell(4).font = { italic: true, color: { argb: 'FF' + colors.gray } }
        currentRow++
      }
      
      currentRow++
      
      // ═══════════════════════════════════════════════════════════════
      // FOOTER
      // ═══════════════════════════════════════════════════════════════
      ws.mergeCells(`A${currentRow}:K${currentRow}`)
      const footerCell = ws.getCell(`A${currentRow}`)
      footerCell.value = '© Gayrat Stroy House ERP System | Hisobot avtomatik tarzda yaratildi'
      footerCell.font = { italic: true, size: 10, color: { argb: 'FF' + colors.gray } }
      footerCell.alignment = { horizontal: 'center' }
      
      // Set column widths - YANADA KENGAYTIRILGAN
      ws.columns = [
        { width: 6 },   // A - №
        { width: 14 },  // B - Sana
        { width: 22 },  // C - Vaqt / Chek № (items) - KENGAYTIRILDI
        { width: 28 },  // D - Chek raqami (sales) / Tovar nomi (items) / Turi (debt) - KENGAYTIRILDI
        { width: 35 },  // E - Tovarlar soni (sales) / Artikul (items) / Summa (debt)
        { width: 22 },  // F - Umumiy summa (sales) / Miqdor (items) / Qarz oldin (debt) - KENGAYTIRILDI
        { width: 20 },  // G - To'langan (sales) / O'lchov (items) / Qarz keyin (debt) - KENGAYTIRILDI
        { width: 20 },  // H - Qarz (sales) / Narx (items) / O'zgarish (debt) - KENGAYTIRILDI
        { width: 18 },  // I - Holat (sales) / Chegirma (items)
        { width: 50 },  // J - Summa (items) / Izoh (debt) - JUDA KENGAYTIRILDI
        { width: 5 },   // K - Extra
      ]
      
      // Generate and download file
      const buffer = await workbook.xlsx.writeBuffer()
      const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const fileName = `${selectedCustomer.name.replace(/\s+/g, '_')}_hisobot_${formatDateTashkent(new Date()).replace(/\./g, '-')}.xlsx`
      saveAs(blob, fileName)
      
      toast.dismiss()
      toast.success('Hisobot muvaffaqiyatli yuklandi!')
    } catch (error) {
      toast.dismiss()
      toast.error('Xatolik yuz berdi')
      console.error('Excel export error:', error)
    }
  }

  // Fetch customer payments (keeping for backward compatibility)
  const { data: customerPayments } = useQuery({
    queryKey: ['customer-payments', selectedCustomer?.id],
    queryFn: async () => {
      if (!selectedCustomer) return null
      const response = await api.get(`/customers/${selectedCustomer.id}/payments`)
      return response.data
    },
    enabled: !!selectedCustomer && showDetailDialog,
  })

  // Create customer mutation
  const createCustomer = useMutation({
    mutationFn: async (data: CustomerFormData) => {
      // Filter out empty strings - backend expects null, not empty string
      const cleanData: any = {}
      Object.entries(data).forEach(([key, value]) => {
        if (value !== '' && value !== undefined && value !== null) {
          cleanData[key] = value
        }
      })
      const response = await api.post('/customers', cleanData)
      return response.data
    },
    onSuccess: () => {
      toast.success(t('customerAdded'))
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      setShowAddDialog(false)
      reset()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      // Handle validation errors (array of objects)
      if (Array.isArray(detail)) {
        const messages = detail.map((e: any) => {
          if (typeof e === 'string') return e
          if (typeof e.msg === 'string') return e.msg
          return t('validationError')
        })
        toast.error(messages.join(', '))
      } else if (typeof detail === 'string') {
        toast.error(detail)
      } else {
        toast.error(t('errorOccurred'))
      }
    },
  })

  // Update customer mutation
  const updateCustomer = useMutation({
    mutationFn: async (data: CustomerFormData) => {
      if (!editingCustomer) return
      const cleanData: any = {}
      Object.entries(data).forEach(([key, value]) => {
        if (value !== '' && value !== undefined && value !== null) {
          cleanData[key] = value
        }
      })
      const response = await api.patch(`/customers/${editingCustomer.id}`, cleanData)
      return response.data
    },
    onSuccess: () => {
      toast.success(t('customerUpdated'))
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['debtors-summary'] })
      setShowAddDialog(false)
      setEditingCustomer(null)
      reset()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        const messages = detail.map((e: any) => typeof e.msg === 'string' ? e.msg : t('validationError'))
        toast.error(messages.join(', '))
      } else {
        toast.error(typeof detail === 'string' ? detail : t('errorOccurred'))
      }
    },
  })

  // Delete customer mutation
  const deleteCustomer = useMutation({
    mutationFn: async (customerId: number) => {
      const response = await api.delete(`/customers/${customerId}`)
      return response.data
    },
    onSuccess: () => {
      toast.success('Mijoz o\'chirildi!')
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['debtors-summary'] })
      setShowDeleteConfirm(false)
      setSelectedCustomer(null)
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Mijozni o\'chirib bo\'lmadi')
    },
  })

  // Pay debt mutation
  const payDebt = useMutation({
    mutationFn: async (data: PaymentFormData) => {
      if (!selectedCustomer) return
      const response = await api.post(`/customers/${selectedCustomer.id}/pay-debt`, data)
      return response.data
    },
    onSuccess: (data) => {
      toast.success(`To'lov qabul qilindi! Qolgan qarz: ${formatMoney(data.current_debt)}`)
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['debtors-summary'] })
      queryClient.invalidateQueries({ queryKey: ['customer-payments'] })
      setShowPaymentDialog(false)
      setPaymentAmountDisplay('')
      resetPayment()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        const messages = detail.map((e: any) => typeof e.msg === 'string' ? e.msg : 'Xatolik')
        toast.error(messages.join(', '))
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Xatolik yuz berdi')
      }
    },
  })

  const onSubmit = (data: CustomerFormData) => {
    if (editingCustomer) {
      updateCustomer.mutate(data)
    } else {
      createCustomer.mutate(data)
    }
  }
  const onPaymentSubmit = (data: PaymentFormData) => payDebt.mutate(data)

  const handlePayClick = (customer: Customer) => {
    setSelectedCustomer(customer)
    setPaymentValue('amount', customer.current_debt)
    setPaymentAmountDisplay(formatInputNumber(customer.current_debt))
    setShowPaymentDialog(true)
  }

  const handleEditClick = (customer: Customer) => {
    setEditingCustomer(customer)
    setValue('name', customer.name)
    setValue('phone', customer.phone)
    setValue('phone_secondary', customer.phone_secondary || '')
    setValue('telegram_id', customer.telegram_id || '')
    setValue('company_name', customer.company_name || '')
    setValue('email', customer.email || '')
    setValue('address', customer.address || '')
    setValue('customer_type', customer.customer_type)
    setValue('credit_limit', customer.credit_limit || 0)
    setValue('manager_id', customer.manager_id || undefined)
    setShowAddDialog(true)
  }

  const handleDeleteClick = (customer: Customer) => {
    setSelectedCustomer(customer)
    setShowDeleteConfirm(true)
  }

  const handleDetailClick = (customer: Customer) => {
    setSelectedCustomer(customer)
    setShowDetailDialog(true)
  }

  const getTypeBadge = (type: string) => {
    const normalizedType = type?.toUpperCase() || 'REGULAR'
    const badges: Record<string, { variant: 'warning' | 'primary' | 'secondary', label: string }> = {
      'VIP': { variant: 'warning', label: 'VIP' },
      'WHOLESALE': { variant: 'primary', label: 'Ulgurji' },
      'REGULAR': { variant: 'secondary', label: 'Oddiy' },
    }
    const b = badges[normalizedType] || badges.REGULAR
    return <Badge variant={b.variant}>{b.label}</Badge>
  }

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 lg:gap-4">
        <h1 className="text-xl lg:text-pos-xl font-bold">{t('customers')}</h1>
        <Button size="lg" onClick={() => setShowAddDialog(true)} className="w-full sm:w-auto">
          <Plus className="w-5 h-5 mr-2" />
          {t('addCustomer')}
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-2 lg:gap-4">
        <Card>
          <CardContent className="p-2.5 lg:p-4 flex flex-col lg:flex-row items-center gap-2 lg:gap-4">
            <div className="p-2 lg:p-3 bg-primary/10 rounded-xl">
              <User className="w-4 h-4 lg:w-6 lg:h-6 text-primary" />
            </div>
            <div className="text-center lg:text-left">
              <p className="text-xs lg:text-sm text-text-secondary">{t('customers')}</p>
              <p className="text-sm lg:text-pos-lg font-bold">{customersData?.total || 0}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-2.5 lg:p-4 flex flex-col lg:flex-row items-center gap-2 lg:gap-4">
            <div className="p-2 lg:p-3 bg-danger/10 rounded-xl">
              <CreditCard className="w-4 h-4 lg:w-6 lg:h-6 text-danger" />
            </div>
            <div className="text-center lg:text-left">
              <p className="text-xs lg:text-sm text-text-secondary">{t('debt')}</p>
              <p className="text-sm lg:text-pos-lg font-bold">{debtorsData?.data?.length || 0}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-2.5 lg:p-4 flex flex-col lg:flex-row items-center gap-2 lg:gap-4">
            <div className="p-2 lg:p-3 bg-warning/10 rounded-xl">
              <Banknote className="w-4 h-4 lg:w-6 lg:h-6 text-warning" />
            </div>
            <div className="text-center lg:text-left">
              <p className="text-xs lg:text-sm text-text-secondary">{t('totalDebt')}</p>
              <p className="text-xs lg:text-pos-lg font-bold text-danger truncate">{formatMoney(debtorsData?.total_debt || 0)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-3 lg:p-4">
          <div className="flex flex-col sm:flex-row gap-2 lg:gap-4 items-stretch sm:items-center">
            <div className="flex-1">
              <Input
                icon={<Search className="w-4 h-4 lg:w-5 lg:h-5" />}
                placeholder={t('search') + '...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="text-sm lg:text-base"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <select
                className="flex-1 sm:flex-none min-h-[44px] lg:min-h-btn px-3 lg:px-4 py-2 lg:py-3 border-2 border-border rounded-xl text-sm lg:text-pos-base"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="">{t('all')}</option>
                <option value="REGULAR">{t('retail')}</option>
                <option value="VIP">VIP</option>
                <option value="WHOLESALE">{t('wholesale')}</option>
              </select>
              <select
                className="flex-1 sm:flex-none min-h-[44px] lg:min-h-btn px-3 lg:px-4 py-2 lg:py-3 border-2 border-border rounded-xl text-sm lg:text-pos-base"
                value={filterSellerId}
                onChange={(e) => setFilterSellerId(e.target.value ? Number(e.target.value) : '')}
              >
                <option value="">{t('all')} {t('seller').toLowerCase()}</option>
                {sellersData?.data?.map((seller: UserType) => (
                  <option key={seller.id} value={seller.id}>
                    {seller.first_name} {seller.last_name}
                  </option>
                ))}
              </select>
              <Button
                variant={showDebtorsOnly ? 'danger' : 'outline'}
                onClick={() => setShowDebtorsOnly(!showDebtorsOnly)}
                className="text-sm lg:text-base"
              >
                <CreditCard className="w-4 h-4 lg:w-5 lg:h-5 lg:mr-2" />
                <span className="hidden lg:inline">Faqat qarzdorlar</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Customers List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="space-y-3">
          {customersData?.data?.map((customer: Customer) => (
            <Card key={customer.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4 flex-1">
                    <div className="p-3 bg-primary/10 rounded-full">
                      <User className="w-6 h-6 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-semibold text-pos-base">{customer.name}</p>
                        {getTypeBadge(customer.customer_type)}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-text-secondary">
                        <span className="flex items-center gap-1">
                          <Phone className="w-4 h-4" />
                          {formatPhone(customer.phone)}
                        </span>
                        {customer.company_name && (
                          <span className="flex items-center gap-1">
                            <Building className="w-4 h-4" />
                            {customer.company_name}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-center hidden md:block">
                      <p className="text-xs text-text-secondary">{t('totalPurchases')}</p>
                      <p className="font-semibold text-primary">{formatMoney(customer.total_purchases)}</p>
                    </div>

                    {customer.current_debt > 0 && (
                      <div className="text-center">
                        <p className="text-xs text-text-secondary">{t('debt')}</p>
                        <p className="font-bold text-danger">{formatMoney(customer.current_debt)}</p>
                      </div>
                    )}

                    {customer.advance_balance > 0 && (
                      <div className="text-center">
                        <p className="text-xs text-text-secondary">{t('advanceBalance')}</p>
                        <p className="font-bold text-success">{formatMoney(customer.advance_balance)}</p>
                      </div>
                    )}

                    <div className="flex gap-2">
                      {customer.current_debt > 0 && (
                        <Button variant="success" size="sm" onClick={() => handlePayClick(customer)}>
                          <Banknote className="w-4 h-4 mr-1" />
                          {t('payment')}
                        </Button>
                      )}
                      <Button variant="outline" size="sm" onClick={() => handleEditClick(customer)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleDetailClick(customer)}>
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteClick(customer)}
                        className="text-danger hover:bg-danger hover:text-white"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {customersData?.data?.length === 0 && (
            <div className="text-center py-12">
              <User className="w-16 h-16 mx-auto text-text-secondary opacity-50 mb-4" />
              <p className="text-text-secondary">{t('noCustomersFound')}</p>
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      {customersData && customersData.total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>{t('previous')}</Button>
          <span className="px-4">{page} / {Math.ceil(customersData.total / 20)}</span>
          <Button variant="outline" disabled={page >= Math.ceil(customersData.total / 20)} onClick={() => setPage(page + 1)}>{t('next')}</Button>
        </div>
      )}

      {/* Add/Edit Customer Dialog */}
      <Dialog open={showAddDialog} onOpenChange={(open) => {
        setShowAddDialog(open)
        if (!open) {
          setEditingCustomer(null)
          reset()
        }
      }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingCustomer ? t('editCustomerTitle') : t('addCustomerTitle')}</DialogTitle>
            <DialogDescription>{t('enterCustomerDetails')}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <label className="font-medium">{t('customerName')} *</label>
              <Input {...register('name', { required: t('nameRequired') })} placeholder={t('fullName')} />
              {errors.name && <p className="text-danger text-sm">{errors.name.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="font-medium">{t('phone')} *</label>
                <Input {...register('phone', { required: t('phoneRequired') })} placeholder="+998 90 123 45 67" />
              </div>
              <div className="space-y-2">
                <label className="font-medium">{t('secondaryPhone')}</label>
                <Input {...register('phone_secondary')} placeholder="+998 90 123 45 67" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="font-medium">{t('telegramId')}</label>
                <Input {...register('telegram_id')} placeholder={t('telegramPlaceholder')} />
              </div>
              <div className="space-y-2">
                <label className="font-medium">{t('emailLabel')}</label>
                <Input {...register('email')} type="email" placeholder="email@example.com" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="font-medium">{t('companyName')}</label>
                <Input {...register('company_name')} placeholder={t('companyPlaceholder')} />
              </div>
              <div className="space-y-2">
                <label className="font-medium">{t('address')}</label>
                <Input {...register('address')} placeholder={t('fullAddress')} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="font-medium">{t('customerType')}</label>
                <select {...register('customer_type')} className="w-full min-h-btn px-4 py-3 border-2 border-border rounded-pos">
                  <option value="REGULAR">{t('regular')}</option>
                  <option value="VIP">{t('vip')}</option>
                  <option value="WHOLESALE">{t('wholesale')}</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="font-medium">{t('creditLimit')}</label>
                <Input type="number" {...register('credit_limit', { valueAsNumber: true })} placeholder="0" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="font-medium flex items-center gap-2">
                <Users className="w-4 h-4" />
                {t('assignedSeller')}
              </label>
              <select {...register('manager_id', { valueAsNumber: true })} className="w-full min-h-btn px-4 py-3 border-2 border-border rounded-pos">
                <option value="">{t('notAssigned')}</option>
                {sellersData?.data?.map((seller: UserType) => (
                  <option key={seller.id} value={seller.id}>
                    {seller.first_name} {seller.last_name}
                  </option>
                ))}
              </select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => {
                setShowAddDialog(false)
                setEditingCustomer(null)
                reset()
              }}>
                {t('cancel')}
              </Button>
              <Button type="submit" disabled={createCustomer.isPending || updateCustomer.isPending}>
                {(createCustomer.isPending || updateCustomer.isPending) ? t('saving') : t('save')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-danger">
              <AlertTriangle className="w-5 h-5" />
              {t('deleteCustomerTitle')}
            </DialogTitle>
            <DialogDescription>
              {t('confirmDelete')} <strong>{selectedCustomer?.name}</strong> {t('confirmDeleteCustomer')}
              {selectedCustomer && selectedCustomer.current_debt > 0 && (
                <span className="block mt-2 text-danger">
                  {t('customerHasDebt')} ({formatMoney(selectedCustomer.current_debt)})
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteConfirm(false)}>
              {t('cancel')}
            </Button>
            <Button
              variant="danger"
              onClick={() => selectedCustomer && deleteCustomer.mutate(selectedCustomer.id)}
              disabled={deleteCustomer.isPending}
            >
              {deleteCustomer.isPending ? t('deleting') : t('delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent className="max-w-[380px]">
          <DialogHeader>
            <DialogTitle className="pr-6">{t('acceptPayment')}</DialogTitle>
          </DialogHeader>

          {selectedCustomer && (
            <div className="bg-gradient-to-r from-red-50 to-orange-50 p-3 rounded-lg mb-3">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white rounded-full">
                  <User className="w-4 h-4 text-red-500" />
                </div>
                <div>
                  <p className="font-semibold text-sm">{selectedCustomer.name}</p>
                  <p className="text-xs text-gray-500">{formatPhone(selectedCustomer.phone)}</p>
                </div>
              </div>
              <div className="mt-2 p-2 bg-white rounded-lg text-center">
                <p className="text-xs text-gray-500">{t('currentDebt')}:</p>
                <p className="text-lg font-bold text-red-600">{formatMoney(selectedCustomer.current_debt)}</p>
              </div>
            </div>
          )}

          <form onSubmit={handlePaymentSubmit(onPaymentSubmit)} className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">{t('paymentAmount')} *</label>
              <input
                type="text"
                inputMode="numeric"
                value={paymentAmountDisplay}
                onChange={(e) => {
                  const raw = e.target.value.replace(/\s/g, '')
                  const num = parseFloat(raw) || 0
                  setPaymentAmountDisplay(num > 0 ? formatInputNumber(num) : '')
                  setPaymentValue('amount', num)
                }}
                placeholder={t('enterAmount')}
                className="w-full h-11 px-3 text-base font-bold text-center border-2 border-gray-200 rounded-lg focus:border-blue-500 outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">{t('paymentType')}</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'CASH', label: t('cash'), icon: Banknote },
                  { value: 'CARD', label: t('card'), icon: CreditCard },
                  { value: 'TRANSFER', label: t('transfer'), icon: Building },
                ].map((pt) => (
                  <label key={pt.value} className="cursor-pointer">
                    <input type="radio" {...registerPayment('payment_type')} value={pt.value} className="sr-only peer" />
                    <div className="flex flex-col items-center gap-1 p-2 border-2 border-gray-200 rounded-lg peer-checked:border-blue-500 peer-checked:bg-blue-50 transition-colors">
                      <pt.icon className="w-4 h-4" />
                      <span className="text-xs">{pt.label}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">{t('notesLabel')}</label>
              <Input {...registerPayment('description')} placeholder={t('optionalNote')} className="text-sm" />
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowPaymentDialog(false)}
                className="flex-1 h-10 border-2 border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                type="submit"
                disabled={payDebt.isPending}
                className="flex-1 h-10 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
              >
                {payDebt.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Banknote className="w-4 h-4" />}
                {t('accept')}
              </button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Customer Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('customerDetails')}</DialogTitle>
            <DialogDescription>{t('fullHistoryAndStats')}</DialogDescription>
          </DialogHeader>

          {selectedCustomer && (
            <div className="space-y-6">
              {/* Customer Info Header */}
              <div className="bg-gradient-to-r from-primary/10 to-primary/5 p-4 rounded-pos">
                <div className="flex items-start justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-4">
                    <div className="p-4 bg-white rounded-full shadow-sm">
                      <User className="w-8 h-8 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-pos-lg font-bold">{selectedCustomer.name}</h3>
                        {getTypeBadge(selectedCustomer.customer_type)}
                      </div>
                      <div className="flex flex-wrap gap-4 mt-2 text-sm text-text-secondary">
                        <span className="flex items-center gap-1">
                          <Phone className="w-4 h-4" />
                          {formatPhone(selectedCustomer.phone)}
                        </span>
                        {selectedCustomer.company_name && (
                          <span className="flex items-center gap-1">
                            <Building className="w-4 h-4" />
                            {selectedCustomer.company_name}
                          </span>
                        )}
                        {selectedCustomer.email && (
                          <span className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            {selectedCustomer.email}
                          </span>
                        )}
                        {selectedCustomer.telegram_id && (
                          <span className="flex items-center gap-1">
                            <span className="w-4 h-4 text-blue-500 font-bold text-xs">TG</span>
                            {selectedCustomer.telegram_id}
                          </span>
                        )}
                        {selectedCustomer.address && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {selectedCustomer.address}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  {selectedCustomer.current_debt > 0 && (
                    <Button variant="success" onClick={() => {
                      setShowDetailDialog(false)
                      setTimeout(() => handlePayClick(selectedCustomer), 100)
                    }}>
                      <Banknote className="w-4 h-4 mr-2" />
                      {t('acceptPayment')}
                    </Button>
                  )}
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-sm text-text-secondary">{t('totalPurchases')}</p>
                    <p className="text-pos-lg font-bold text-primary">{formatMoney(selectedCustomer.total_purchases)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-sm text-text-secondary">{t('currentDebt')}</p>
                    <p className={cn("text-pos-lg font-bold", selectedCustomer.current_debt > 0 ? "text-danger" : "text-success")}>
                      {formatMoney(selectedCustomer.current_debt)}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-sm text-text-secondary">{t('advanceBalance')}</p>
                    <p className="text-pos-lg font-bold text-success">{formatMoney(selectedCustomer.advance_balance)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-sm text-text-secondary">{t('creditLimit')}</p>
                    <p className="text-pos-lg font-bold">{formatMoney(selectedCustomer.credit_limit)}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Professional Excel Export Button */}
              <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-pos p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                      <FileSpreadsheet className="w-5 h-5 text-green-600" />
                      {t('downloadFullReport')}
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {t('allSalesProductsDebtInExcel')}
                    </p>
                  </div>
                  <Button
                    variant="success"
                    onClick={exportCustomerDataToExcel}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    {t('downloadExcel')}
                  </Button>
                </div>
              </div>

              {/* Sales History */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold flex items-center gap-2">
                    <ShoppingCart className="w-5 h-5" />
                    {t('salesHistory')} ({customerSales?.data?.length || 0})
                  </h4>
                </div>
                {loadingSales ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                ) : customerSales?.data && customerSales.data.length > 0 ? (
                  <div className="border border-border rounded-pos overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="w-10"></th>
                          <th className="px-4 py-3 text-left text-sm font-medium">{t('date')}</th>
                          <th className="px-4 py-3 text-left text-sm font-medium">{t('receiptNo')}</th>
                          <th className="px-4 py-3 text-center text-sm font-medium">{t('products')}</th>
                          <th className="px-4 py-3 text-right text-sm font-medium">{t('amount')}</th>
                          <th className="px-4 py-3 text-right text-sm font-medium">{t('paidAmount')}</th>
                          <th className="px-4 py-3 text-right text-sm font-medium">{t('debtAmount')}</th>
                          <th className="px-4 py-3 text-center text-sm font-medium">{t('status')}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {customerSales.data.map((sale: Sale) => (
                          <React.Fragment key={sale.id}>
                            <tr
                              className="hover:bg-gray-50 cursor-pointer"
                              onClick={() => loadSaleItems(sale.id)}
                            >
                              <td className="px-2 py-3 text-center">
                                {loadingSaleItems === sale.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                                ) : expandedSaleId === sale.id ? (
                                  <ChevronDown className="w-4 h-4 mx-auto text-blue-600" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 mx-auto text-gray-400" />
                                )}
                              </td>
                              <td className="px-4 py-3 text-sm">
                                <div className="flex items-center gap-1">
                                  <Calendar className="w-4 h-4 text-text-secondary" />
                                  {formatDateTashkent(sale.created_at)}
                                </div>
                                <div className="text-xs text-text-secondary ml-5">
                                  {formatTimeTashkent(sale.created_at)}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-sm font-medium">{sale.sale_number}</td>
                              <td className="px-4 py-3 text-sm text-center">
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-xs">
                                  <Package className="w-3 h-3" />
                                  {sale.items_count || '?'}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-sm text-right font-semibold">{formatMoney(sale.total_amount)}</td>
                              <td className="px-4 py-3 text-sm text-right text-success">{formatMoney(sale.paid_amount)}</td>
                              <td className="px-4 py-3 text-sm text-right text-danger">
                                {sale.debt_amount > 0 ? formatMoney(sale.debt_amount) : '-'}
                              </td>
                              <td className="px-4 py-3 text-center">
                                <Badge variant={
                                  sale.payment_status === 'PAID' ? 'success' :
                                  sale.payment_status === 'DEBT' ? 'danger' :
                                  sale.payment_status === 'PARTIAL' ? 'warning' : 'secondary'
                                }>
                                  {sale.payment_status === 'PAID' ? t('paid') :
                                   sale.payment_status === 'DEBT' ? t('onDebt') :
                                   sale.payment_status === 'PARTIAL' ? t('partial') : sale.payment_status}
                                </Badge>
                              </td>
                            </tr>
                            {/* Expanded items */}
                            {expandedSaleId === sale.id && saleItems[sale.id] && (
                              <tr key={`${sale.id}-items`}>
                                <td colSpan={8} className="p-0">
                                  <div className="bg-blue-50 p-4 border-t border-blue-200">
                                    <h5 className="font-medium text-sm mb-2 text-blue-800">{t('productsList')}:</h5>
                                    <table className="w-full text-sm">
                                      <thead>
                                        <tr className="text-gray-600">
                                          <th className="text-left py-1 px-2">{t('product')}</th>
                                          <th className="text-center py-1 px-2">{t('quantity')}</th>
                                          <th className="text-right py-1 px-2">{t('price')}</th>
                                          <th className="text-right py-1 px-2">{t('discount')}</th>
                                          <th className="text-right py-1 px-2">{t('total')}</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {saleItems[sale.id].map((item: SaleItem) => (
                                          <tr key={item.id} className="border-t border-blue-200">
                                            <td className="py-2 px-2 font-medium">{item.product_name}</td>
                                            <td className="py-2 px-2 text-center">{item.quantity} {item.uom_symbol}</td>
                                            <td className="py-2 px-2 text-right">{formatMoney(item.unit_price)}</td>
                                            <td className="py-2 px-2 text-right text-orange-600">
                                              {item.discount_amount > 0 ? `-${formatMoney(item.discount_amount)}` : '-'}
                                            </td>
                                            <td className="py-2 px-2 text-right font-semibold">{formatMoney(item.total_price)}</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-text-secondary bg-gray-50 rounded-pos">
                    <ShoppingCart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>{t('noSalesFound')}</p>
                  </div>
                )}
              </div>

              {/* Payment/Debt History with Running Balance */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Banknote className="w-5 h-5" />
                    {t('debtPaymentHistory')} ({customerDebtHistory?.data?.length || 0})
                  </h4>
                </div>
                {customerDebtHistory?.data && customerDebtHistory.data.length > 0 ? (
                  <div className="border border-border rounded-pos overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-medium">{t('date')}</th>
                          <th className="px-4 py-3 text-left text-sm font-medium">{t('movementType')}</th>
                          <th className="px-4 py-3 text-right text-sm font-medium">{t('amount')}</th>
                          <th className="px-4 py-3 text-right text-sm font-medium">{t('debtBefore')}</th>
                          <th className="px-4 py-3 text-right text-sm font-medium">{t('debtAfter')}</th>
                          <th className="px-4 py-3 text-left text-sm font-medium">{t('notesLabel')}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {customerDebtHistory.data.map((record: DebtRecord) => {
                          const isPayment = record.transaction_type === 'PAYMENT' || record.transaction_type === 'DEBT_PAYMENT'
                          const isSale = record.transaction_type === 'SALE'

                          return (
                            <tr key={record.id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm">
                                <div>{formatDateTashkent(record.created_at)}</div>
                                <div className="text-xs text-text-secondary">{formatTimeTashkent(record.created_at)}</div>
                              </td>
                              <td className="px-4 py-3 text-sm">
                                <Badge variant={isPayment ? 'success' : isSale ? 'warning' : 'secondary'}>
                                  {isPayment ? t('paymentTransaction') : isSale ? t('purchaseTransaction') : record.transaction_type}
                                </Badge>
                              </td>
                              <td className={cn(
                                "px-4 py-3 text-sm text-right font-semibold",
                                isPayment ? "text-green-600" : "text-red-600"
                              )}>
                                {isPayment ? '-' : '+'}{formatMoney(Math.abs(record.amount))}
                              </td>
                              <td className="px-4 py-3 text-sm text-right text-gray-500">
                                {formatMoney(record.balance_before)}
                              </td>
                              <td className={cn(
                                "px-4 py-3 text-sm text-right font-semibold",
                                record.balance_after > 0 ? "text-red-600" : "text-green-600"
                              )}>
                                {formatMoney(record.balance_after)}
                              </td>
                              <td className="px-4 py-3 text-sm text-text-secondary max-w-xs truncate">
                                {record.description || '-'}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-text-secondary bg-gray-50 rounded-pos">
                    <Banknote className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>{t('noHistoryFound')}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}