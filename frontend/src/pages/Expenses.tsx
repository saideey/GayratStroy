import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Pencil, Trash2, RotateCcw, History, X, Filter, Download,
  TrendingDown, TrendingUp, DollarSign, ChevronDown, ChevronRight,
  Tag, AlertTriangle, Loader2, Search, Calendar, Eye
} from 'lucide-react'
import toast from 'react-hot-toast'
import { Button, Input, Card, CardContent, Badge, Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui'
import api from '@/services/api'
import { downloadExcel } from '@/services/exportService'
import { formatMoney, formatDateTashkent, formatDateTimeTashkent, cn } from '@/lib/utils'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ExpenseCategory {
  id: number
  name: string
  description?: string
  color: string
  icon?: string
  is_active: boolean
  created_at: string
}

interface EditLog {
  id: number
  action: 'created' | 'updated' | 'deleted' | 'restored'
  comment: string
  changed_at: string
  changed_by_name: string
  old_title?: string
  old_amount?: number
  old_currency?: string
  old_category_id?: number
  old_expense_date?: string
  new_title?: string
  new_amount?: number
  new_currency?: string
  new_category_id?: number
  new_expense_date?: string
}

interface Expense {
  id: number
  title: string
  description?: string
  amount: number
  currency: 'uzs' | 'usd'
  usd_rate?: number
  amount_uzs?: number
  expense_date: string
  category_id: number
  category_name: string
  category_color: string
  created_by_id: number
  created_by_name: string
  is_deleted: boolean
  deleted_at?: string
  deleted_by_name?: string
  delete_comment?: string
  created_at: string
  updated_at: string
  edit_logs?: EditLog[]
}

interface ProfitSummary {
  total_revenue: number
  total_expenses: number
  net_profit: number
  profit_margin: number
  by_category: { category_id: number; category_name: string; category_color: string; total_uzs: number; count: number }[]
}

// ─── Constants ────────────────────────────────────────────────────────────────

const PRESET_COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#ef4444',
  '#f59e0b', '#10b981', '#3b82f6', '#06b6d4',
  '#84cc16', '#f97316', '#6b7280', '#14b8a6',
]

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  created:  { label: 'Yaratildi',   color: 'bg-green-100 text-green-700' },
  updated:  { label: 'Yangilandi',  color: 'bg-blue-100 text-blue-700' },
  deleted:  { label: "O'chirildi",  color: 'bg-red-100 text-red-700' },
  restored: { label: 'Tiklandi',    color: 'bg-yellow-100 text-yellow-700' },
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function ExpensesPage() {
  const queryClient = useQueryClient()

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [currency, setCurrency] = useState('')
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [page, setPage] = useState(1)

  // UI state
  const [activeTab, setActiveTab] = useState<'expenses' | 'categories' | 'profit'>('expenses')
  const [showExpenseModal, setShowExpenseModal] = useState(false)
  const [showCategoryModal, setShowCategoryModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [excelLoading, setExcelLoading] = useState(false)
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
  const [editingCategory, setEditingCategory] = useState<ExpenseCategory | null>(null)
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null)
  const [deleteComment, setDeleteComment] = useState('')

  // Expense form
  const [expenseForm, setExpenseForm] = useState({
    title: '', description: '', amount: '',
    currency: 'uzs', usd_rate: '', expense_date: new Date().toISOString().split('T')[0],
    category_id: '', comment: '',
  })

  // Category form
  const [categoryForm, setCategoryForm] = useState({
    name: '', description: '', color: '#6366f1', icon: '',
  })

  // ─── Queries ──────────────────────────────────────────────────────────────

  const { data: categoriesData, isLoading: loadingCategories } = useQuery({
    queryKey: ['expense-categories'],
    queryFn: async () => {
      const res = await api.get('/expenses/categories?include_inactive=true')
      return res.data.data as ExpenseCategory[]
    },
  })

  const { data: expensesData, isLoading: loadingExpenses } = useQuery({
    queryKey: ['expenses', page, selectedCategory, startDate, endDate, currency, includeDeleted],
    queryFn: async () => {
      const params: Record<string, any> = { page, per_page: 20 }
      if (selectedCategory) params.category_id = selectedCategory
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      if (currency) params.currency = currency
      if (includeDeleted) params.include_deleted = true
      const res = await api.get('/expenses', { params })
      return res.data.data
    },
  })

  const { data: profitData, isLoading: loadingProfit } = useQuery({
    queryKey: ['profit-summary', startDate, endDate],
    queryFn: async () => {
      const params: Record<string, any> = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const res = await api.get('/expenses/profit-summary', { params })
      return res.data.data as ProfitSummary
    },
    enabled: activeTab === 'profit',
  })

  const { data: logsData, isLoading: loadingLogs } = useQuery({
    queryKey: ['expense-logs', selectedExpense?.id],
    queryFn: async () => {
      const res = await api.get(`/expenses/${selectedExpense!.id}/logs`)
      return res.data.data as EditLog[]
    },
    enabled: !!selectedExpense && showLogsModal,
  })

  // ─── Mutations ────────────────────────────────────────────────────────────

  const createExpense = useMutation({
    mutationFn: (data: any) => api.post('/expenses', data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expenses'] }); toast.success('Chiqim yozildi'); closeExpenseModal() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const updateExpense = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => api.put(`/expenses/${id}`, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expenses'] }); toast.success('Chiqim yangilandi'); closeExpenseModal() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const deleteExpense = useMutation({
    mutationFn: ({ id, comment }: { id: number; comment: string }) =>
      api.delete(`/expenses/${id}`, { data: { comment } }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expenses'] }); toast.success("Chiqim o'chirildi"); setShowDeleteModal(false); setDeleteComment('') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const restoreExpense = useMutation({
    mutationFn: (id: number) => api.post(`/expenses/${id}/restore`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expenses'] }); toast.success('Chiqim tiklandi') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const createCategory = useMutation({
    mutationFn: (data: any) => api.post('/expenses/categories', data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expense-categories'] }); toast.success('Kategoriya yaratildi'); closeCategoryModal() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const updateCategory = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => api.put(`/expenses/categories/${id}`, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expense-categories'] }); toast.success('Kategoriya yangilandi'); closeCategoryModal() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const deleteCategory = useMutation({
    mutationFn: (id: number) => api.delete(`/expenses/categories/${id}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['expense-categories'] }); toast.success('Kategoriya deaktiv qilindi') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  // ─── Handlers ─────────────────────────────────────────────────────────────

  const openExpenseModal = (expense?: Expense) => {
    if (expense) {
      setEditingExpense(expense)
      setExpenseForm({
        title: expense.title,
        description: expense.description || '',
        amount: String(expense.amount),
        currency: expense.currency,
        usd_rate: String(expense.usd_rate || ''),
        expense_date: expense.expense_date,
        category_id: String(expense.category_id),
        comment: '',
      })
    } else {
      setEditingExpense(null)
      setExpenseForm({
        title: '', description: '', amount: '', currency: 'uzs',
        usd_rate: '', expense_date: new Date().toISOString().split('T')[0],
        category_id: '', comment: '',
      })
    }
    setShowExpenseModal(true)
  }

  const closeExpenseModal = () => { setShowExpenseModal(false); setEditingExpense(null) }

  const openCategoryModal = (cat?: ExpenseCategory) => {
    if (cat) {
      setEditingCategory(cat)
      setCategoryForm({ name: cat.name, description: cat.description || '', color: cat.color, icon: cat.icon || '' })
    } else {
      setEditingCategory(null)
      setCategoryForm({ name: '', description: '', color: '#6366f1', icon: '' })
    }
    setShowCategoryModal(true)
  }

  const closeCategoryModal = () => { setShowCategoryModal(false); setEditingCategory(null) }

  const handleExpenseSubmit = () => {
    if (!expenseForm.title || !expenseForm.amount || !expenseForm.category_id || !expenseForm.expense_date) {
      toast.error('Barcha majburiy maydonlarni to\'ldiring')
      return
    }
    if (editingExpense && !expenseForm.comment) {
      toast.error('O\'zgartirish sababi (izoh) kiritilishi shart')
      return
    }
    if (expenseForm.currency === 'usd' && !expenseForm.usd_rate) {
      toast.error('USD da yozilganda kurs kiritilishi shart')
      return
    }

    const payload: any = {
      title: expenseForm.title,
      description: expenseForm.description || undefined,
      amount: parseFloat(expenseForm.amount),
      currency: expenseForm.currency,
      expense_date: expenseForm.expense_date,
      category_id: parseInt(expenseForm.category_id),
    }
    if (expenseForm.currency === 'usd') payload.usd_rate = parseFloat(expenseForm.usd_rate)
    if (editingExpense) {
      payload.comment = expenseForm.comment
      updateExpense.mutate({ id: editingExpense.id, data: payload })
    } else {
      createExpense.mutate(payload)
    }
  }

  const handleCategorySubmit = () => {
    if (!categoryForm.name) { toast.error('Nom kiritilishi shart'); return }
    if (editingCategory) {
      updateCategory.mutate({ id: editingCategory.id, data: categoryForm })
    } else {
      createCategory.mutate(categoryForm)
    }
  }

  const handleDeleteConfirm = () => {
    if (!deleteComment.trim()) { toast.error('Izoh kiritilishi shart'); return }
    if (selectedExpense) deleteExpense.mutate({ id: selectedExpense.id, comment: deleteComment })
  }

  const clearFilters = () => {
    setSelectedCategory(null); setStartDate(''); setEndDate(''); setCurrency(''); setIncludeDeleted(false); setPage(1)
  }

  const hasFilters = selectedCategory || startDate || endDate || currency || includeDeleted

  const categories = categoriesData || []
  const activeCategories = categories.filter(c => c.is_active)
  const expenses: Expense[] = expensesData?.items || []
  const summary = expensesData?.summary
  const totalPages = expensesData?.total_pages || 1

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Chiqimlar</h1>
          <p className="text-text-secondary text-sm mt-1">Xarajatlarni kategoriyalar bo'yicha boshqarish</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={excelLoading}
            onClick={async () => {
              setExcelLoading(true)
              try {
                const params = new URLSearchParams()
                if (selectedCategory) params.append('category_id', String(selectedCategory))
                if (startDate) params.append('start_date', startDate)
                if (endDate) params.append('end_date', endDate)
                if (currency) params.append('currency', currency)
                await downloadExcel(`/expenses/export/excel?${params}`, `chiqimlar_${new Date().toISOString().split('T')[0]}.xlsx`)
                toast.success('Excel yuklab olindi')
              } catch (e: any) {
                toast.error(e.message || 'Xatolik')
              } finally {
                setExcelLoading(false)
              }
            }}
            className="gap-2"
          >
            {excelLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Excel
          </Button>
          <Button onClick={() => openExpenseModal()} className="gap-2">
            <Plus className="w-4 h-4" /> Chiqim yozish
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
        {[
          { key: 'expenses', label: 'Chiqimlar' },
          { key: 'categories', label: 'Kategoriyalar' },
          { key: 'profit', label: 'Sof foyda' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === tab.key ? 'bg-white shadow text-primary' : 'text-text-secondary hover:text-text-primary'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ══════════ CHIQIMLAR TAB ══════════ */}
      {activeTab === 'expenses' && (
        <div className="space-y-4">

          {/* Summary cards */}
          {summary && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-text-secondary">Jami (so'm)</p>
                  <p className="text-xl font-bold text-danger mt-1">{formatMoney(summary.total_uzs || 0)}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-text-secondary">Jami (dollar)</p>
                  <p className="text-xl font-bold text-warning mt-1">${Number(summary.total_usd || 0).toFixed(2)}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-text-secondary">UZS ekvivalent (jami)</p>
                  <p className="text-xl font-bold text-primary mt-1">{formatMoney(summary.total_uzs_equivalent || 0)}</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-3 items-end">
                {/* Kategoriya filter */}
                <div className="flex-1 min-w-[160px]">
                  <label className="text-xs font-medium text-text-secondary mb-1 block">Kategoriya</label>
                  <select
                    value={selectedCategory || ''}
                    onChange={e => { setSelectedCategory(e.target.value ? parseInt(e.target.value) : null); setPage(1) }}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  >
                    <option value="">Barchasi</option>
                    {activeCategories.map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                    ))}
                  </select>
                </div>

                {/* Boshlanish sanasi */}
                <div className="flex-1 min-w-[140px]">
                  <label className="text-xs font-medium text-text-secondary mb-1 block">Dan</label>
                  <input
                    type="date" value={startDate}
                    onChange={e => { setStartDate(e.target.value); setPage(1) }}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                {/* Tugash sanasi */}
                <div className="flex-1 min-w-[140px]">
                  <label className="text-xs font-medium text-text-secondary mb-1 block">Gacha</label>
                  <input
                    type="date" value={endDate}
                    onChange={e => { setEndDate(e.target.value); setPage(1) }}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                {/* Valyuta */}
                <div className="min-w-[120px]">
                  <label className="text-xs font-medium text-text-secondary mb-1 block">Valyuta</label>
                  <select
                    value={currency}
                    onChange={e => { setCurrency(e.target.value); setPage(1) }}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  >
                    <option value="">Barchasi</option>
                    <option value="uzs">So'm</option>
                    <option value="usd">Dollar</option>
                  </select>
                </div>

                {/* Include deleted */}
                <label className="flex items-center gap-2 cursor-pointer pb-2">
                  <input
                    type="checkbox" checked={includeDeleted}
                    onChange={e => { setIncludeDeleted(e.target.checked); setPage(1) }}
                    className="w-4 h-4 rounded border-gray-300 text-primary"
                  />
                  <span className="text-sm text-text-secondary">O'chirilganlar</span>
                </label>

                {/* Clear filters */}
                {hasFilters && (
                  <Button variant="outline" size="sm" onClick={clearFilters} className="gap-1 pb-2">
                    <X className="w-3 h-3" /> Tozalash
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Expenses table */}
          <Card>
            <CardContent className="p-0">
              {loadingExpenses ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : expenses.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-text-secondary">
                  <TrendingDown className="w-12 h-12 mb-3 opacity-30" />
                  <p className="font-medium">Chiqimlar topilmadi</p>
                  <p className="text-sm">Filtrni o'zgartiring yoki yangi chiqim yozing</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50">
                        <th className="text-left px-4 py-3 font-medium text-text-secondary">Sana</th>
                        <th className="text-left px-4 py-3 font-medium text-text-secondary">Sarlavha</th>
                        <th className="text-left px-4 py-3 font-medium text-text-secondary">Kategoriya</th>
                        <th className="text-right px-4 py-3 font-medium text-text-secondary">Summa</th>
                        <th className="text-left px-4 py-3 font-medium text-text-secondary">Kim yozdi</th>
                        <th className="text-left px-4 py-3 font-medium text-text-secondary">Holat</th>
                        <th className="text-right px-4 py-3 font-medium text-text-secondary">Amallar</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expenses.map(expense => (
                        <tr
                          key={expense.id}
                          className={cn(
                            'border-b border-gray-50 hover:bg-gray-50/50 transition-colors',
                            expense.is_deleted && 'opacity-50 bg-red-50/30'
                          )}
                        >
                          <td className="px-4 py-3 text-text-secondary whitespace-nowrap">
                            {formatDateTashkent(expense.expense_date)}
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-medium text-text-primary">{expense.title}</div>
                            {expense.description && (
                              <div className="text-xs text-text-secondary truncate max-w-[200px]">{expense.description}</div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-medium text-white"
                              style={{ backgroundColor: expense.category_color || '#6366f1' }}
                            >
                              {expense.category_name}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right font-semibold whitespace-nowrap">
                            {expense.currency === 'usd' ? (
                              <div>
                                <div className="text-warning">${Number(expense.amount).toFixed(2)}</div>
                                {expense.amount_uzs && (
                                  <div className="text-xs text-text-secondary">{formatMoney(expense.amount_uzs)}</div>
                                )}
                              </div>
                            ) : (
                              <span className="text-danger">{formatMoney(expense.amount)}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-text-secondary text-xs">{expense.created_by_name}</td>
                          <td className="px-4 py-3">
                            {expense.is_deleted ? (
                              <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-lg text-xs font-medium">
                                <Trash2 className="w-3 h-3" /> O'chirilgan
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-lg text-xs font-medium">
                                Aktiv
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center justify-end gap-1">
                              {/* Ko'rish */}
                              <button
                                onClick={() => { setSelectedExpense(expense); setShowDetailModal(true) }}
                                className="p-1.5 rounded-lg hover:bg-gray-100 text-text-secondary hover:text-primary transition-colors"
                                title="Ko'rish"
                              >
                                <Eye className="w-4 h-4" />
                              </button>

                              {/* Tarix */}
                              <button
                                onClick={() => { setSelectedExpense(expense); setShowLogsModal(true) }}
                                className="p-1.5 rounded-lg hover:bg-gray-100 text-text-secondary hover:text-blue-600 transition-colors"
                                title="O'zgartirish tarixi"
                              >
                                <History className="w-4 h-4" />
                              </button>

                              {!expense.is_deleted ? (
                                <>
                                  {/* Tahrirlash */}
                                  <button
                                    onClick={() => openExpenseModal(expense)}
                                    className="p-1.5 rounded-lg hover:bg-gray-100 text-text-secondary hover:text-warning transition-colors"
                                    title="Tahrirlash"
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </button>

                                  {/* O'chirish */}
                                  <button
                                    onClick={() => { setSelectedExpense(expense); setShowDeleteModal(true) }}
                                    className="p-1.5 rounded-lg hover:bg-red-50 text-text-secondary hover:text-danger transition-colors"
                                    title="O'chirish"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </>
                              ) : (
                                /* Tiklash */
                                <button
                                  onClick={() => restoreExpense.mutate(expense.id)}
                                  className="p-1.5 rounded-lg hover:bg-green-50 text-text-secondary hover:text-success transition-colors"
                                  title="Tiklash"
                                >
                                  <RotateCcw className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                Oldingi
              </Button>
              <span className="text-sm text-text-secondary px-3">{page} / {totalPages}</span>
              <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                Keyingi
              </Button>
            </div>
          )}
        </div>
      )}

      {/* ══════════ KATEGORIYALAR TAB ══════════ */}
      {activeTab === 'categories' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => openCategoryModal()} className="gap-2">
              <Plus className="w-4 h-4" /> Kategoriya qo'shish
            </Button>
          </div>

          {loadingCategories ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map(cat => (
                <Card key={cat.id} className={cn(!cat.is_active && 'opacity-60')}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                          style={{ backgroundColor: cat.color + '20', border: `2px solid ${cat.color}` }}
                        >
                          {cat.icon || <Tag className="w-4 h-4" style={{ color: cat.color }} />}
                        </div>
                        <div>
                          <h3 className="font-semibold text-text-primary">{cat.name}</h3>
                          {cat.description && (
                            <p className="text-xs text-text-secondary mt-0.5">{cat.description}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => openCategoryModal(cat)}
                          className="p-1.5 rounded-lg hover:bg-gray-100 text-text-secondary hover:text-warning transition-colors"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        {cat.is_active && (
                          <button
                            onClick={() => {
                              if (confirm(`"${cat.name}" kategoriyasini deaktiv qilasizmi?`))
                                deleteCategory.mutate(cat.id)
                            }}
                            className="p-1.5 rounded-lg hover:bg-red-50 text-text-secondary hover:text-danger transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full inline-block"
                        style={{ backgroundColor: cat.color }}
                      />
                      <span className="text-xs text-text-secondary font-mono">{cat.color}</span>
                      {!cat.is_active && (
                        <span className="ml-auto text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                          Deaktiv
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ══════════ SOF FOYDA TAB ══════════ */}
      {activeTab === 'profit' && (
        <div className="space-y-4">
          {/* Date filter for profit */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-3 items-end">
                <div className="flex-1 min-w-[140px]">
                  <label className="text-xs font-medium text-text-secondary mb-1 block">Dan</label>
                  <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary" />
                </div>
                <div className="flex-1 min-w-[140px]">
                  <label className="text-xs font-medium text-text-secondary mb-1 block">Gacha</label>
                  <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary" />
                </div>
                {(startDate || endDate) && (
                  <Button variant="outline" size="sm" onClick={() => { setStartDate(''); setEndDate('') }}>
                    <X className="w-3 h-3 mr-1" /> Tozalash
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {loadingProfit ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : profitData ? (
            <>
              {/* Main profit cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="border-l-4 border-l-green-500">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-text-secondary">Sotuv daromadi</p>
                      <TrendingUp className="w-5 h-5 text-green-500" />
                    </div>
                    <p className="text-2xl font-bold text-green-600">{formatMoney(profitData.total_revenue)}</p>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-red-500">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-text-secondary">Jami chiqimlar</p>
                      <TrendingDown className="w-5 h-5 text-red-500" />
                    </div>
                    <p className="text-2xl font-bold text-red-600">{formatMoney(profitData.total_expenses)}</p>
                  </CardContent>
                </Card>

                <Card className={cn('border-l-4', profitData.net_profit >= 0 ? 'border-l-primary' : 'border-l-orange-500')}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-text-secondary">Sof foyda</p>
                      <DollarSign className={cn('w-5 h-5', profitData.net_profit >= 0 ? 'text-primary' : 'text-orange-500')} />
                    </div>
                    <p className={cn('text-2xl font-bold', profitData.net_profit >= 0 ? 'text-primary' : 'text-orange-600')}>
                      {formatMoney(profitData.net_profit)}
                    </p>
                  </CardContent>
                </Card>

                <Card className="border-l-4 border-l-purple-500">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-text-secondary">Rentabellik</p>
                      <span className="text-purple-500 font-bold text-lg">%</span>
                    </div>
                    <p className="text-2xl font-bold text-purple-600">{Number(profitData.profit_margin).toFixed(1)}%</p>
                  </CardContent>
                </Card>
              </div>

              {/* Category breakdown */}
              {profitData.by_category.length > 0 && (
                <Card>
                  <CardContent className="p-4">
                    <h3 className="font-semibold mb-4">Kategoriyalar bo'yicha chiqimlar</h3>
                    <div className="space-y-3">
                      {profitData.by_category
                        .filter(c => c.total_uzs > 0)
                        .map(cat => {
                          const pct = profitData.total_expenses > 0
                            ? (Number(cat.total_uzs) / Number(profitData.total_expenses)) * 100
                            : 0
                          return (
                            <div key={cat.category_id}>
                              <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-2">
                                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.category_color || '#6366f1' }} />
                                  <span className="text-sm font-medium">{cat.category_name}</span>
                                  <span className="text-xs text-text-secondary">({cat.count} ta)</span>
                                </div>
                                <div className="text-right">
                                  <span className="text-sm font-semibold text-danger">{formatMoney(cat.total_uzs)}</span>
                                  <span className="text-xs text-text-secondary ml-2">{pct.toFixed(1)}%</span>
                                </div>
                              </div>
                              <div className="w-full bg-gray-100 rounded-full h-2">
                                <div
                                  className="h-2 rounded-full transition-all"
                                  style={{ width: `${pct}%`, backgroundColor: cat.category_color || '#6366f1' }}
                                />
                              </div>
                            </div>
                          )
                        })}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : null}
        </div>
      )}

      {/* ══════════════════════════════════
           MODALS
      ══════════════════════════════════ */}

      {/* Expense Create/Edit Modal */}
      <Dialog open={showExpenseModal} onOpenChange={setShowExpenseModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingExpense ? 'Chiqimni tahrirlash' : 'Yangi chiqim'}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Sarlavha */}
            <div>
              <label className="text-sm font-medium mb-1 block">Sarlavha *</label>
              <input
                value={expenseForm.title} onChange={e => setExpenseForm({ ...expenseForm, title: e.target.value })}
                placeholder="Masalan: Mart oyi elektr energiyasi"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>

            {/* Kategoriya */}
            <div>
              <label className="text-sm font-medium mb-1 block">Kategoriya *</label>
              <select
                value={expenseForm.category_id}
                onChange={e => setExpenseForm({ ...expenseForm, category_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                <option value="">Kategoriyani tanlang</option>
                {activeCategories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                ))}
              </select>
            </div>

            {/* Summa va valyuta */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium mb-1 block">Summa *</label>
                <input
                  type="number" min="0"
                  value={expenseForm.amount} onChange={e => setExpenseForm({ ...expenseForm, amount: e.target.value })}
                  placeholder="0"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Valyuta *</label>
                <select
                  value={expenseForm.currency}
                  onChange={e => setExpenseForm({ ...expenseForm, currency: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                >
                  <option value="uzs">So'm (UZS)</option>
                  <option value="usd">Dollar (USD)</option>
                </select>
              </div>
            </div>

            {/* USD kurs (faqat USD tanlanganda) */}
            {expenseForm.currency === 'usd' && (
              <div>
                <label className="text-sm font-medium mb-1 block">1 USD = ? so'm *</label>
                <input
                  type="number" min="0"
                  value={expenseForm.usd_rate} onChange={e => setExpenseForm({ ...expenseForm, usd_rate: e.target.value })}
                  placeholder="Masalan: 12700"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
                {expenseForm.amount && expenseForm.usd_rate && (
                  <p className="text-xs text-text-secondary mt-1">
                    ≈ {formatMoney(parseFloat(expenseForm.amount) * parseFloat(expenseForm.usd_rate))}
                  </p>
                )}
              </div>
            )}

            {/* Sana */}
            <div>
              <label className="text-sm font-medium mb-1 block">Sana *</label>
              <input
                type="date"
                value={expenseForm.expense_date} onChange={e => setExpenseForm({ ...expenseForm, expense_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>

            {/* Izoh */}
            <div>
              <label className="text-sm font-medium mb-1 block">Izoh</label>
              <textarea
                value={expenseForm.description} onChange={e => setExpenseForm({ ...expenseForm, description: e.target.value })}
                placeholder="Qo'shimcha ma'lumot (ixtiyoriy)"
                rows={2}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"
              />
            </div>

            {/* O'zgartirish sababi (faqat edit uchun, MAJBURIY) */}
            {editingExpense && (
              <div className="border border-orange-200 bg-orange-50 rounded-lg p-3">
                <label className="text-sm font-medium mb-1 block text-orange-800">
                  O'zgartirish sababi * <span className="font-normal text-orange-600">(majburiy)</span>
                </label>
                <textarea
                  value={expenseForm.comment} onChange={e => setExpenseForm({ ...expenseForm, comment: e.target.value })}
                  placeholder="Nima uchun o'zgartirilmoqda?"
                  rows={2}
                  className="w-full px-3 py-2 border border-orange-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-orange-500/20 focus:border-orange-400 resize-none"
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeExpenseModal}>Bekor qilish</Button>
            <Button
              onClick={handleExpenseSubmit}
              disabled={createExpense.isPending || updateExpense.isPending}
            >
              {(createExpense.isPending || updateExpense.isPending) ? (
                <><Loader2 className="w-4 h-4 animate-spin mr-2" />Saqlanmoqda...</>
              ) : editingExpense ? 'Saqlash' : 'Yozish'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Category Create/Edit Modal */}
      <Dialog open={showCategoryModal} onOpenChange={setShowCategoryModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingCategory ? 'Kategoriyani tahrirlash' : 'Yangi kategoriya'}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium mb-1 block">Nomi *</label>
              <input
                value={categoryForm.name} onChange={e => setCategoryForm({ ...categoryForm, name: e.target.value })}
                placeholder="Masalan: Elektr energiyasi"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">Tavsif</label>
              <input
                value={categoryForm.description} onChange={e => setCategoryForm({ ...categoryForm, description: e.target.value })}
                placeholder="Qo'shimcha izoh (ixtiyoriy)"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">Emoji belgisi</label>
              <input
                value={categoryForm.icon} onChange={e => setCategoryForm({ ...categoryForm, icon: e.target.value })}
                placeholder="Masalan: ⚡ 🏠 👥"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Rang</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {PRESET_COLORS.map(color => (
                  <button
                    key={color}
                    onClick={() => setCategoryForm({ ...categoryForm, color })}
                    className={cn(
                      'w-8 h-8 rounded-lg transition-all',
                      categoryForm.color === color && 'ring-2 ring-offset-2 ring-gray-400 scale-110'
                    )}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="color" value={categoryForm.color}
                  onChange={e => setCategoryForm({ ...categoryForm, color: e.target.value })}
                  className="w-10 h-10 rounded-lg border border-gray-200 cursor-pointer p-0.5"
                />
                <span className="text-sm text-text-secondary font-mono">{categoryForm.color}</span>
                {categoryForm.icon && (
                  <div
                    className="ml-auto w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                    style={{ backgroundColor: categoryForm.color + '20', border: `2px solid ${categoryForm.color}` }}
                  >
                    {categoryForm.icon}
                  </div>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeCategoryModal}>Bekor qilish</Button>
            <Button
              onClick={handleCategorySubmit}
              disabled={createCategory.isPending || updateCategory.isPending}
            >
              {(createCategory.isPending || updateCategory.isPending) ? (
                <><Loader2 className="w-4 h-4 animate-spin mr-2" />Saqlanmoqda...</>
              ) : 'Saqlash'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm Modal */}
      <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-danger">
              <AlertTriangle className="w-5 h-5" /> Chiqimni o'chirish
            </DialogTitle>
          </DialogHeader>
          <div className="py-2 space-y-3">
            <p className="text-text-secondary text-sm">
              <strong className="text-text-primary">"{selectedExpense?.title}"</strong> chiqimini o'chirmoqchimisiz?
              Bu amal bekor qilinishi mumkin (tiklash orqali).
            </p>
            <div>
              <label className="text-sm font-medium mb-1 block text-danger">
                O'chirish sababi * <span className="text-text-secondary font-normal">(majburiy)</span>
              </label>
              <textarea
                value={deleteComment} onChange={e => setDeleteComment(e.target.value)}
                placeholder="Nima uchun o'chirilmoqda?"
                rows={3}
                className="w-full px-3 py-2 border border-red-200 rounded-lg text-sm focus:ring-2 focus:ring-danger/20 focus:border-danger resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowDeleteModal(false); setDeleteComment('') }}>Bekor qilish</Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteExpense.isPending}
            >
              {deleteExpense.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />}
              O'chirish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Chiqim tafsiloti</DialogTitle>
          </DialogHeader>
          {selectedExpense && (
            <div className="py-2 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><p className="text-text-secondary">Sarlavha</p><p className="font-semibold">{selectedExpense.title}</p></div>
                <div><p className="text-text-secondary">Sana</p><p className="font-semibold">{formatDateTashkent(selectedExpense.expense_date)}</p></div>
                <div>
                  <p className="text-text-secondary">Summa</p>
                  <p className="font-semibold text-danger">
                    {selectedExpense.currency === 'usd'
                      ? `$${Number(selectedExpense.amount).toFixed(2)} (${formatMoney(selectedExpense.amount_uzs || 0)})`
                      : formatMoney(selectedExpense.amount)}
                  </p>
                </div>
                <div>
                  <p className="text-text-secondary">Kategoriya</p>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium text-white" style={{ backgroundColor: selectedExpense.category_color }}>
                    {selectedExpense.category_name}
                  </span>
                </div>
                <div><p className="text-text-secondary">Kim yozdi</p><p className="font-semibold">{selectedExpense.created_by_name}</p></div>
                <div><p className="text-text-secondary">Yozilgan vaqt</p><p className="font-semibold">{formatDateTimeTashkent(selectedExpense.created_at)}</p></div>
              </div>
              {selectedExpense.description && (
                <div className="border-t pt-3">
                  <p className="text-text-secondary text-sm">Izoh</p>
                  <p className="text-sm mt-1">{selectedExpense.description}</p>
                </div>
              )}
              {selectedExpense.is_deleted && (
                <div className="border border-red-200 bg-red-50 rounded-lg p-3 text-sm">
                  <p className="font-semibold text-red-700 mb-1">O'chirilgan</p>
                  <p className="text-red-600">Kim: {selectedExpense.deleted_by_name}</p>
                  <p className="text-red-600">Vaqt: {formatDateTimeTashkent(selectedExpense.deleted_at)}</p>
                  {selectedExpense.delete_comment && <p className="text-red-600">Sabab: {selectedExpense.delete_comment}</p>}
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailModal(false)}>Yopish</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Logs Modal */}
      <Dialog open={showLogsModal} onOpenChange={setShowLogsModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="w-5 h-5" /> O'zgartirish tarixi
              {selectedExpense && <span className="text-text-secondary font-normal text-sm">— {selectedExpense.title}</span>}
            </DialogTitle>
          </DialogHeader>

          {loadingLogs ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
            </div>
          ) : logsData && logsData.length > 0 ? (
            <div className="py-2 space-y-3">
              {logsData.map(log => (
                <div key={log.id} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={cn('px-2 py-0.5 rounded-full text-xs font-semibold', ACTION_LABELS[log.action]?.color)}>
                        {ACTION_LABELS[log.action]?.label || log.action}
                      </span>
                      <span className="text-sm font-medium">{log.changed_by_name}</span>
                    </div>
                    <span className="text-xs text-text-secondary">{formatDateTimeTashkent(log.changed_at)}</span>
                  </div>

                  <p className="text-sm text-text-secondary bg-gray-50 rounded-lg px-3 py-2 italic">
                    "{log.comment}"
                  </p>

                  {/* O'zgargan qiymatlar */}
                  {log.action === 'updated' && (
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                      {log.old_title !== log.new_title && (
                        <>
                          <div className="bg-red-50 rounded-lg px-2 py-1.5">
                            <p className="text-red-500 font-medium mb-0.5">Eski sarlavha</p>
                            <p className="text-red-700">{log.old_title}</p>
                          </div>
                          <div className="bg-green-50 rounded-lg px-2 py-1.5">
                            <p className="text-green-500 font-medium mb-0.5">Yangi sarlavha</p>
                            <p className="text-green-700">{log.new_title}</p>
                          </div>
                        </>
                      )}
                      {String(log.old_amount) !== String(log.new_amount) && (
                        <>
                          <div className="bg-red-50 rounded-lg px-2 py-1.5">
                            <p className="text-red-500 font-medium mb-0.5">Eski summa</p>
                            <p className="text-red-700">{log.old_currency === 'uzs' ? formatMoney(log.old_amount || 0) : `$${log.old_amount}`}</p>
                          </div>
                          <div className="bg-green-50 rounded-lg px-2 py-1.5">
                            <p className="text-green-500 font-medium mb-0.5">Yangi summa</p>
                            <p className="text-green-700">{log.new_currency === 'uzs' ? formatMoney(log.new_amount || 0) : `$${log.new_amount}`}</p>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-text-secondary">
              <History className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p>O'zgartirish tarixi topilmadi</p>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLogsModal(false)}>Yopish</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
