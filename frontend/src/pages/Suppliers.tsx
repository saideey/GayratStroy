import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Pencil, Trash2, Phone, Building2, Search,
  TrendingDown, TrendingUp, History, AlertTriangle,
  Loader2, X, ChevronRight, User, Star, Eye,
  RotateCcw, Download, Package, BarChart3, Calendar,
  ArrowUpRight, ArrowDownRight, Banknote, FileText,
  ShoppingCart, ChevronDown, ChevronUp, Wallet, RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  Button, Card, CardContent,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui'
import api from '@/services/api'
import { downloadExcel } from '@/services/exportService'
import { formatMoney, formatDateTashkent, formatDateTimeTashkent, cn } from '@/lib/utils'

// ─── Types ────────────────────────────────────────────────────────────────────
interface Supplier {
  id: number; name: string; company_name?: string; contact_person?: string
  phone?: string; address?: string; city?: string; inn?: string
  current_debt: number; advance_balance: number; net_balance: number
  balance_type: 'debt' | 'advance' | 'zero'
  rating: number; is_active: boolean; notes?: string
}
interface SupplierStats {
  // Joriy holat
  current_debt: number; current_advance: number; net_balance: number
  balance_type: 'debt' | 'advance' | 'zero'
  // Filter bo'yicha
  period_debt_written: number; period_paid: number; period_net: number
  transaction_count: number
  last_transaction_date?: string; last_transaction_type?: string; last_transaction_amount?: number
  // Kirimlar
  purchase_count: number; unique_products: number
  total_items_received: number; total_purchase_amount: number
  purchase_docs: PurchaseDoc[]
  top_products: TopProduct[]
  monthly: { year: number; month: number; debt: number; paid: number; tx_count: number }[]
  filter_start?: string; filter_end?: string
}
interface PurchaseDoc {
  document_number: string; date?: string; total_amount: number; items_count: number
  items: { product_name: string; quantity: number; uom_symbol: string; unit_cost: number; total_cost: number }[]
}
interface TopProduct {
  product_id: number; product_name: string; total_quantity: number
  total_amount: number; uom_symbol: string; times_ordered: number
}
interface Transaction {
  id: number; transaction_type: 'debt' | 'payment' | 'return'
  amount: number; currency: string; amount_uzs?: number
  transaction_date: string; comment: string; created_by_name: string
  is_deleted: boolean; deleted_by_name?: string; delete_comment?: string; created_at: string
}

// ─── Constants ────────────────────────────────────────────────────────────────
const TX_CONF = {
  debt:    { label: 'Qarz',      color: 'bg-red-100 text-red-700',    icon: TrendingDown },
  payment: { label: "To'lov",    color: 'bg-green-100 text-green-700', icon: TrendingUp },
  return:  { label: 'Qaytarish', color: 'bg-blue-100 text-blue-700',   icon: RotateCcw },
}
const MONTHS_UZ = ['Yan','Feb','Mar','Apr','May','Iyun','Iyul','Avg','Sen','Okt','Noy','Dek']

// ─── Balance Badge ────────────────────────────────────────────────────────────
function BalanceBadge({ debt, advance, netBalance, balanceType, large = false }: {
  debt: number; advance: number; netBalance: number; balanceType: string; large?: boolean
}) {
  if (balanceType === 'advance' && advance > 0) {
    return (
      <div className={cn('flex flex-col', large ? 'gap-1' : 'gap-0.5')}>
        <span className={cn('font-bold text-green-600', large ? 'text-2xl' : 'text-sm')}>
          ✓ Qarsiz
        </span>
        <span className={cn('text-green-500', large ? 'text-base' : 'text-xs')}>
          Avans: +{formatMoney(advance)}
        </span>
        <span className="text-xs text-text-secondary">(Ular bizga qarzli)</span>
      </div>
    )
  }
  if (balanceType === 'debt' && debt > 0) {
    return (
      <div className={cn('flex flex-col', large ? 'gap-1' : 'gap-0.5')}>
        <span className={cn('font-bold text-red-600', large ? 'text-2xl' : 'text-sm')}>
          {formatMoney(debt)}
        </span>
        <span className="text-xs text-red-400">(Biz ularga qarzlimiz)</span>
      </div>
    )
  }
  return <span className={cn('font-bold text-gray-500', large ? 'text-2xl' : 'text-sm')}>Hisob-kitob yo'q</span>
}

// ─── Mini Chart ───────────────────────────────────────────────────────────────
function BarChart({ data }: { data: SupplierStats['monthly'] }) {
  if (!data.length) return (
    <div className="flex items-center justify-center h-24 text-xs text-text-secondary">Ma'lumot yo'q</div>
  )
  const maxVal = Math.max(...data.flatMap(d => [d.debt, d.paid]), 1)
  return (
    <div className="flex items-end gap-1 h-24 pt-2">
      {data.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-0.5 min-w-0">
          <div className="w-full flex gap-0.5 items-end" style={{ height: '60px' }}>
            <div title={`Qarz: ${formatMoney(d.debt)}`}
              className="flex-1 bg-red-400/80 rounded-t-sm hover:bg-red-500 cursor-help"
              style={{ height: `${Math.max(2, (d.debt / maxVal) * 60)}px` }} />
            <div title={`To'lov: ${formatMoney(d.paid)}`}
              className="flex-1 bg-green-400/80 rounded-t-sm hover:bg-green-500 cursor-help"
              style={{ height: `${Math.max(2, (d.paid / maxVal) * 60)}px` }} />
          </div>
          <span className="text-[9px] text-text-secondary truncate w-full text-center">
            {MONTHS_UZ[d.month - 1]}{data.length > 12 ? ` '${String(d.year).slice(-2)}` : ''}
          </span>
        </div>
      ))}
    </div>
  )
}

// ─── Purchase Doc Card ────────────────────────────────────────────────────────
function PurchaseDocCard({ doc }: { doc: PurchaseDoc }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-50/50 text-left">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
            <FileText className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-medium">#{doc.document_number}</p>
            {doc.date && <p className="text-xs text-text-secondary">{formatDateTashkent(doc.date)}</p>}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-semibold text-danger">{formatMoney(doc.total_amount)}</p>
            <p className="text-xs text-text-secondary">{doc.items.length} xil · {Math.round(doc.items_count)} dona</p>
          </div>
          {open ? <ChevronUp className="w-4 h-4 text-text-secondary" /> : <ChevronDown className="w-4 h-4 text-text-secondary" />}
        </div>
      </button>
      {open && (
        <div className="border-t border-gray-100 bg-gray-50/50">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-gray-100">
              <th className="text-left px-3 py-2 text-text-secondary font-medium">Mahsulot</th>
              <th className="text-right px-3 py-2 text-text-secondary font-medium">Miqdor</th>
              <th className="text-right px-3 py-2 text-text-secondary font-medium">Narx</th>
              <th className="text-right px-3 py-2 text-text-secondary font-medium">Jami</th>
            </tr></thead>
            <tbody>
              {doc.items.map((item, i) => (
                <tr key={i} className={i % 2 === 1 ? 'bg-white/60' : ''}>
                  <td className="px-3 py-2 font-medium">{item.product_name}</td>
                  <td className="px-3 py-2 text-right">{item.quantity} {item.uom_symbol}</td>
                  <td className="px-3 py-2 text-right text-text-secondary">{formatMoney(item.unit_cost)}</td>
                  <td className="px-3 py-2 text-right font-semibold text-danger">{formatMoney(item.total_cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ─── Supplier Form ────────────────────────────────────────────────────────────
function SupplierFormModal({ open, onClose, supplier, onSaved }: {
  open: boolean; onClose: () => void; supplier: Supplier | null; onSaved: (s: Supplier) => void
}) {
  const [form, setForm] = useState({
    name: supplier?.name || '', company_name: supplier?.company_name || '',
    contact_person: supplier?.contact_person || '', phone: supplier?.phone || '',
    address: supplier?.address || '', city: supplier?.city || '',
    inn: supplier?.inn || '', rating: supplier?.rating || 5, notes: supplier?.notes || '',
  })
  const save = useMutation({
    mutationFn: (d: any) => supplier ? api.put(`/suppliers/${supplier.id}`, d) : api.post('/suppliers', d),
    onSuccess: (r) => { onSaved(r.data.data); toast.success(supplier ? 'Yangilandi' : 'Yaratildi') },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader><DialogTitle>{supplier ? "Tahrirlash" : "Yangi ta'minotchi"}</DialogTitle></DialogHeader>
        <div className="space-y-3 py-2">
          <div className="grid grid-cols-2 gap-3">
            {[
              { k:'name', l:"Nomi *", ph:"Aziz Savdo", full:true },
              { k:'company_name', l:'Kompaniya', ph:'Kompaniya nomi', full:false },
              { k:'contact_person', l:"Mas'ul", ph:'Ism familiya', full:false },
              { k:'phone', l:'Telefon', ph:'+998 90 123 45 67', full:false },
              { k:'address', l:'Manzil', ph:"Ko'cha, uy", full:true },
              { k:'city', l:'Shahar', ph:'Toshkent', full:false },
              { k:'inn', l:'INN', ph:'123456789', full:false },
            ].map(f => (
              <div key={f.k} className={f.full ? 'col-span-2' : ''}>
                <label className="text-sm font-medium mb-1 block">{f.l}</label>
                <input value={(form as any)[f.k]} onChange={e => setForm(p => ({ ...p, [f.k]: e.target.value }))}
                  placeholder={f.ph} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary" />
              </div>
            ))}
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Reyting</label>
            <div className="flex gap-2">
              {[1,2,3,4,5].map(s => (
                <button key={s} type="button" onClick={() => setForm(p => ({ ...p, rating: s }))}
                  className={cn('w-10 h-10 rounded-xl border-2 flex items-center justify-center', s <= form.rating ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200')}>
                  <Star className={cn('w-5 h-5', s <= form.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300')} />
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Izoh</label>
            <textarea value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))}
              rows={2} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Bekor</Button>
          <Button onClick={() => save.mutate(form)} disabled={save.isPending}>
            {save.isPending ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />...</> : 'Saqlash'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Transaction Form ─────────────────────────────────────────────────────────
function TxFormModal({ open, onClose, supplierId, defaultType, onSaved, currentDebt, currentAdvance }: {
  open: boolean; onClose: () => void; supplierId: number; defaultType: string
  onSaved: () => void; currentDebt?: number; currentAdvance?: number
}) {
  const [form, setForm] = useState({
    transaction_type: defaultType, amount: '', currency: 'uzs', usd_rate: '',
    transaction_date: new Date().toISOString().split('T')[0], comment: '',
  })
  const save = useMutation({
    mutationFn: (d: any) => api.post(`/suppliers/${supplierId}/transactions`, d),
    onSuccess: () => { toast.success('Yozildi'); onSaved(); onClose() },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })
  const submit = () => {
    if (!form.amount || parseFloat(form.amount) <= 0) { toast.error('Summa kiriting'); return }
    if (form.comment.trim().length < 3) { toast.error('Izoh kamida 3 belgi'); return }
    if (form.currency === 'usd' && !form.usd_rate) { toast.error('Kurs kiriting'); return }
    const p: any = { transaction_type: form.transaction_type, amount: parseFloat(form.amount),
      currency: form.currency, transaction_date: form.transaction_date, comment: form.comment }
    if (form.currency === 'usd') p.usd_rate = parseFloat(form.usd_rate)
    save.mutate(p)
  }

  // To'lov uchun bashorat
  const amountNum = parseFloat(form.amount) || 0
  let forecast = null
  if (form.transaction_type === 'payment' && amountNum > 0) {
    const debt = currentDebt || 0
    const advance = currentAdvance || 0
    if (amountNum <= debt) {
      const remaining = debt - amountNum
      forecast = { type: 'partial', remaining, msg: `Qarz qoldig'i: ${formatMoney(remaining)}` }
    } else if (amountNum > debt) {
      const overpay = amountNum - debt
      forecast = { type: 'overpay', overpay, msg: `Qarz to'liq yopiladi + avans: ${formatMoney(overpay)}` }
    }
  }
  if (form.transaction_type === 'debt' && amountNum > 0) {
    const advance = currentAdvance || 0
    if (advance > 0) {
      if (amountNum <= advance) {
        forecast = { type: 'covered', msg: `Avansdan qoplanadi, qarz kelib chiqmaydi` }
      } else {
        const newDebt = amountNum - advance
        forecast = { type: 'partial_cover', msg: `Avans sarflanadi, yangi qarz: ${formatMoney(newDebt)}` }
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {form.transaction_type === 'debt' ? "Qarz yozish" :
             form.transaction_type === 'payment' ? "To'lov yozish" : "Qaytarish yozish"}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          {/* Joriy balans ko'rsatish */}
          {(currentDebt !== undefined || currentAdvance !== undefined) && (
            <div className="bg-gray-50 rounded-xl p-3 text-sm">
              <p className="text-xs text-text-secondary mb-1.5 font-medium">Joriy holat:</p>
              <div className="flex gap-4">
                {(currentDebt || 0) > 0 && (
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-red-400 rounded-full" />
                    <span className="text-red-600 font-semibold">Qarz: {formatMoney(currentDebt!)}</span>
                  </div>
                )}
                {(currentAdvance || 0) > 0 && (
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-green-400 rounded-full" />
                    <span className="text-green-600 font-semibold">Avans: {formatMoney(currentAdvance!)}</span>
                  </div>
                )}
                {(currentDebt || 0) === 0 && (currentAdvance || 0) === 0 && (
                  <span className="text-text-secondary">Hisob-kitob yo'q</span>
                )}
              </div>
            </div>
          )}

          {/* Tur */}
          <div className="grid grid-cols-3 gap-2">
            {(Object.entries(TX_CONF) as [string, typeof TX_CONF.debt][]).map(([type, c]) => (
              <button key={type} type="button" onClick={() => setForm(p => ({ ...p, transaction_type: type }))}
                className={cn('py-3 rounded-xl text-sm font-medium border-2 flex flex-col items-center gap-1 transition-all',
                  form.transaction_type === type ? 'border-primary bg-primary/5 text-primary' : 'border-gray-200 text-text-secondary hover:border-gray-300')}>
                <c.icon className="w-4 h-4" />{c.label}
              </button>
            ))}
          </div>

          {/* Summa */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium mb-1 block">Summa *</label>
              <input type="number" min="0" value={form.amount}
                onChange={e => setForm(p => ({ ...p, amount: e.target.value }))}
                placeholder="0" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Valyuta</label>
              <select value={form.currency} onChange={e => setForm(p => ({ ...p, currency: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white">
                <option value="uzs">So'm (UZS)</option>
                <option value="usd">Dollar (USD)</option>
              </select>
            </div>
          </div>

          {form.currency === 'usd' && (
            <div>
              <label className="text-sm font-medium mb-1 block">1 USD = ? so'm *</label>
              <input type="number" min="0" value={form.usd_rate}
                onChange={e => setForm(p => ({ ...p, usd_rate: e.target.value }))}
                placeholder="12700" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
            </div>
          )}

          {/* Natija bashorati */}
          {forecast && (
            <div className={cn('rounded-xl p-3 text-sm flex items-start gap-2',
              forecast.type === 'overpay' ? 'bg-green-50 border border-green-200 text-green-700' :
              forecast.type === 'partial' ? 'bg-yellow-50 border border-yellow-200 text-yellow-700' :
              forecast.type === 'covered' ? 'bg-blue-50 border border-blue-200 text-blue-700' :
              'bg-orange-50 border border-orange-200 text-orange-700'
            )}>
              <span className="text-base">
                {forecast.type === 'overpay' ? '✅' : forecast.type === 'partial' ? '⚠️' : '💡'}
              </span>
              <span className="font-medium">{forecast.msg}</span>
            </div>
          )}

          <div>
            <label className="text-sm font-medium mb-1 block">Sana *</label>
            <input type="date" value={form.transaction_date}
              onChange={e => setForm(p => ({ ...p, transaction_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-xl p-3">
            <label className="text-sm font-medium mb-1 block text-orange-800">
              Izoh * <span className="font-normal text-orange-500">(majburiy, min 3 belgi)</span>
            </label>
            <textarea value={form.comment} onChange={e => setForm(p => ({ ...p, comment: e.target.value }))}
              rows={3} placeholder={
                form.transaction_type === 'debt' ? "Masalan: Mart oyiga metall quvur qarzi" :
                form.transaction_type === 'payment' ? "Masalan: Naqd pul to'lov" : "Masalan: Sifatsiz mahsulot qaytarildi"
              }
              className="w-full px-3 py-2 border border-orange-200 rounded-lg text-sm bg-white resize-none" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Bekor</Button>
          <Button onClick={submit} disabled={save.isPending}
            className={cn(form.transaction_type === 'payment' ? 'bg-green-600 hover:bg-green-700' :
              form.transaction_type === 'debt' ? 'bg-red-500 hover:bg-red-600' : '')}>
            {save.isPending ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />Yozilmoqda...</> : 'Yozish'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function SuppliersPage() {
  const qc = useQueryClient()
  const [view, setView] = useState<'list' | 'detail'>('list')
  const [selected, setSelected] = useState<Supplier | null>(null)
  const [search, setSearch] = useState('')
  const [hasDebt, setHasDebt] = useState('')
  const [listPage, setListPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null)
  const [showDeleteSupplier, setShowDeleteSupplier] = useState(false)
  const [showTxModal, setShowTxModal] = useState(false)
  const [txDefaultType, setTxDefaultType] = useState('payment')
  const [showDeleteTx, setShowDeleteTx] = useState(false)
  const [deletingTx, setDeletingTx] = useState<Transaction | null>(null)
  const [deleteTxComment, setDeleteTxComment] = useState('')
  const [txType, setTxType] = useState('')
  const [txFrom, setTxFrom] = useState('')
  const [txTo, setTxTo] = useState('')
  const [showDeletedTx, setShowDeletedTx] = useState(false)
  const [excelLoading, setExcelLoading] = useState(false)
  const [statsTab, setStatsTab] = useState<'overview' | 'purchases' | 'products'>('overview')
  // Statistika uchun alohida sana filtri
  const [statsFrom, setStatsFrom] = useState('')
  const [statsTo, setStatsTo] = useState('')

  const { data: listData, isLoading } = useQuery({
    queryKey: ['suppliers', listPage, search, hasDebt],
    queryFn: async () => {
      const p: any = { page: listPage, per_page: 20 }
      if (search) p.q = search
      if (hasDebt === 'yes') p.has_debt = true
      if (hasDebt === 'no') p.has_debt = false
      return (await api.get('/suppliers', { params: p })).data.data
    },
  })

  const { data: detailData, refetch: refetchDetail } = useQuery({
    queryKey: ['supplier-detail', selected?.id],
    queryFn: async () => (await api.get(`/suppliers/${selected!.id}`)).data.data as Supplier,
    enabled: !!selected,
  })

  const { data: statsData, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['supplier-stats', selected?.id, statsFrom, statsTo],
    queryFn: async () => {
      const p: any = {}
      if (statsFrom) p.start_date = statsFrom
      if (statsTo) p.end_date = statsTo
      const res = await api.get(`/suppliers/${selected!.id}/stats`, { params: p })
      return res.data.data as SupplierStats
    },
    enabled: !!selected && view === 'detail',
    retry: 1,
  })

  const { data: txData, isLoading: txLoading } = useQuery({
    queryKey: ['supplier-tx', selected?.id, txType, txFrom, txTo, showDeletedTx],
    queryFn: async () => {
      const p: any = { page: 1, per_page: 100 }
      if (txType) p.transaction_type = txType
      if (txFrom) p.start_date = txFrom
      if (txTo) p.end_date = txTo
      if (showDeletedTx) p.include_deleted = true
      return (await api.get(`/suppliers/${selected!.id}/transactions`, { params: p })).data.data
    },
    enabled: !!selected && view === 'detail',
  })

  const deleteSupplier = useMutation({
    mutationFn: (id: number) => api.delete(`/suppliers/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['suppliers'] })
      toast.success("O'chirildi"); setShowDeleteSupplier(false); setView('list'); setSelected(null)
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const deleteTxMut = useMutation({
    mutationFn: ({ id, comment }: { id: number; comment: string }) =>
      api.delete(`/suppliers/transactions/${id}`, { data: { comment } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['supplier-tx', selected?.id] })
      qc.invalidateQueries({ queryKey: ['supplier-stats', selected?.id] })
      qc.invalidateQueries({ queryKey: ['supplier-detail', selected?.id] })
      qc.invalidateQueries({ queryKey: ['suppliers'] })
      toast.success("O'chirildi"); setShowDeleteTx(false); setDeleteTxComment(''); setDeletingTx(null)
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Xatolik'),
  })

  const suppliers: Supplier[] = listData?.items || []
  const totalPages = listData?.total_pages || 1
  const totalDebt = listData?.total_debt || 0
  const currentSupplier = detailData || selected
  const transactions: Transaction[] = txData?.items || []
  const stats: SupplierStats | null = statsData || null

  const paymentPercent = stats && stats.period_debt_written > 0
    ? Math.min(100, Math.round((stats.period_paid / stats.period_debt_written) * 100)) : 0

  const openDetail = (s: Supplier) => {
    setSelected(s); setView('detail')
    setTxType(''); setTxFrom(''); setTxTo('')
    setStatsFrom(''); setStatsTo('')
    setShowDeletedTx(false); setStatsTab('overview')
  }
  const handleTxSaved = () => {
    qc.invalidateQueries({ queryKey: ['supplier-tx', selected?.id] })
    qc.invalidateQueries({ queryKey: ['supplier-stats', selected?.id] })
    qc.invalidateQueries({ queryKey: ['supplier-detail', selected?.id] })
    qc.invalidateQueries({ queryKey: ['suppliers'] })
  }
  const handleExcel = async (supplierId?: number) => {
    setExcelLoading(true)
    try {
      if (supplierId) {
        const p = new URLSearchParams()
        if (txFrom) p.append('start_date', txFrom)
        if (txTo) p.append('end_date', txTo)
        if (txType) p.append('transaction_type', txType)
        await downloadExcel(`/suppliers/${supplierId}/export/excel?${p}`, `supplier_${supplierId}.xlsx`)
      } else {
        await downloadExcel('/suppliers/export/excel', `taminotchilar.xlsx`)
      }
      toast.success('Excel yuklab olindi')
    } catch (e: any) { toast.error(e.message || 'Xatolik') }
    finally { setExcelLoading(false) }
  }

  const hasStatsFilter = statsFrom || statsTo

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          {view === 'detail' && (
            <button onClick={() => { setView('list'); setSelected(null) }}
              className="p-2 rounded-xl hover:bg-gray-100"><ChevronRight className="w-5 h-5 rotate-180" /></button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-text-primary">
              {view === 'detail' && currentSupplier ? currentSupplier.name : "Ta'minotchilar"}
            </h1>
            <p className="text-sm text-text-secondary">
              {view === 'detail' && currentSupplier ? currentSupplier.company_name || 'Yetkazib beruvchi' : 'Yetkazib beruvchilar va hisob-kitob'}
            </p>
          </div>
        </div>
        {view === 'list' ? (
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => handleExcel()} disabled={excelLoading} className="gap-2">
              {excelLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Excel
            </Button>
            <Button onClick={() => { setEditingSupplier(null); setShowForm(true) }} className="gap-2">
              <Plus className="w-4 h-4" /> Qo'shish
            </Button>
          </div>
        ) : (
          <div className="flex gap-2 flex-wrap">
            <Button variant="outline" onClick={() => { setEditingSupplier(currentSupplier); setShowForm(true) }} className="gap-2">
              <Pencil className="w-4 h-4" /> Tahrirlash
            </Button>
            <Button variant="outline" onClick={() => handleExcel(selected?.id)} disabled={excelLoading} className="gap-2">
              {excelLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Excel
            </Button>
            <Button onClick={() => { setTxDefaultType('payment'); setShowTxModal(true) }} className="gap-2 bg-green-600 hover:bg-green-700">
              <TrendingUp className="w-4 h-4" /> To'lov
            </Button>
            <Button onClick={() => { setTxDefaultType('debt'); setShowTxModal(true) }} className="gap-2 bg-red-500 hover:bg-red-600">
              <TrendingDown className="w-4 h-4" /> Qarz
            </Button>
          </div>
        )}
      </div>

      {/* ═══ LIST ═══ */}
      {view === 'list' && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Card className="sm:col-span-3">
              <CardContent className="p-4 flex gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input value={search} onChange={e => { setSearch(e.target.value); setListPage(1) }}
                    placeholder="Nom, telefon, kompaniya..."
                    className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary" />
                </div>
                <select value={hasDebt} onChange={e => { setHasDebt(e.target.value); setListPage(1) }}
                  className="px-3 py-2 border border-gray-200 rounded-xl text-sm bg-white">
                  <option value="">Barchasi</option>
                  <option value="yes">Qarzdorlar</option>
                  <option value="no">Qarsiz</option>
                </select>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-red-500">
              <CardContent className="p-4">
                <p className="text-xs text-text-secondary">Umumiy qarz</p>
                <p className="text-xl font-bold text-red-600 mt-0.5">{formatMoney(totalDebt)}</p>
              </CardContent>
            </Card>
          </div>

          <Card><CardContent className="p-0">
            {isLoading ? (
              <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
            ) : suppliers.length === 0 ? (
              <div className="flex flex-col items-center py-16 text-text-secondary">
                <Building2 className="w-12 h-12 mb-3 opacity-20" /><p>Topilmadi</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b bg-gray-50/80">
                    {["Ta'minotchi", 'Kontakt', 'Shahar', 'Balans', 'Reyting', ''].map(h => (
                      <th key={h} className="text-left px-4 py-3 font-medium text-text-secondary">{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {suppliers.map(s => (
                      <tr key={s.id} onClick={() => openDetail(s)}
                        className="border-b border-gray-50 hover:bg-blue-50/30 cursor-pointer transition-colors">
                        <td className="px-4 py-3">
                          <p className="font-semibold">{s.name}</p>
                          {s.company_name && <p className="text-xs text-text-secondary">{s.company_name}</p>}
                        </td>
                        <td className="px-4 py-3 text-text-secondary">
                          {s.phone && <div className="flex items-center gap-1 text-xs"><Phone className="w-3 h-3" />{s.phone}</div>}
                          {s.contact_person && <div className="flex items-center gap-1 text-xs mt-0.5"><User className="w-3 h-3" />{s.contact_person}</div>}
                        </td>
                        <td className="px-4 py-3 text-xs text-text-secondary">{s.city || '—'}</td>
                        <td className="px-4 py-3">
                          <BalanceBadge debt={s.current_debt} advance={s.advance_balance} netBalance={s.net_balance} balanceType={s.balance_type} />
                        </td>
                        <td className="px-4 py-3"><div className="flex gap-0.5">
                          {[1,2,3,4,5].map(n => <Star key={n} className={cn('w-3 h-3', n <= s.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-200')} />)}
                        </div></td>
                        <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                          <div className="flex gap-1 justify-end">
                            <button onClick={() => openDetail(s)} className="p-1.5 hover:bg-primary/10 rounded-lg text-primary"><Eye className="w-4 h-4" /></button>
                            <button onClick={() => { setEditingSupplier(s); setShowForm(true) }} className="p-1.5 hover:bg-gray-100 rounded-lg text-text-secondary hover:text-warning"><Pencil className="w-4 h-4" /></button>
                            <button onClick={() => { setSelected(s); setShowDeleteSupplier(true) }} className="p-1.5 hover:bg-red-50 rounded-lg text-text-secondary hover:text-danger"><Trash2 className="w-4 h-4" /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent></Card>

          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <Button variant="outline" size="sm" disabled={listPage === 1} onClick={() => setListPage(p => p - 1)}>Oldingi</Button>
              <span className="px-3 py-1.5 text-sm">{listPage}/{totalPages}</span>
              <Button variant="outline" size="sm" disabled={listPage === totalPages} onClick={() => setListPage(p => p + 1)}>Keyingi</Button>
            </div>
          )}
        </>
      )}

      {/* ═══ DETAIL ═══ */}
      {view === 'detail' && currentSupplier && (
        <div className="space-y-4">

          {/* ── Balans kartochkalari ── */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

            {/* Joriy holat — asosiy karta */}
            <Card className={cn('sm:col-span-1 border-2',
              stats?.balance_type === 'advance' ? 'border-green-400' :
              stats?.balance_type === 'debt' ? 'border-red-400' : 'border-gray-200')}>
              <CardContent className="p-5">
                <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Joriy holat</p>
                <BalanceBadge
                  debt={stats?.current_debt ?? currentSupplier.current_debt}
                  advance={stats?.current_advance ?? currentSupplier.advance_balance}
                  netBalance={stats?.net_balance ?? currentSupplier.net_balance}
                  balanceType={stats?.balance_type ?? currentSupplier.balance_type}
                  large
                />
                <div className="flex gap-2 mt-4">
                  <button onClick={() => { setTxDefaultType('debt'); setShowTxModal(true) }}
                    className="flex-1 py-2 text-xs rounded-xl bg-red-50 text-red-600 hover:bg-red-100 font-semibold border border-red-100">+ Qarz</button>
                  <button onClick={() => { setTxDefaultType('payment'); setShowTxModal(true) }}
                    className="flex-1 py-2 text-xs rounded-xl bg-green-50 text-green-600 hover:bg-green-100 font-semibold border border-green-100">+ To'lov</button>
                  <button onClick={() => { setTxDefaultType('return'); setShowTxModal(true) }}
                    className="flex-1 py-2 text-xs rounded-xl bg-blue-50 text-blue-600 hover:bg-blue-100 font-semibold border border-blue-100">+ Qayt.</button>
                </div>
              </CardContent>
            </Card>

            {/* Statistika filter */}
            <Card className="sm:col-span-2">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                    {hasStatsFilter ? 'Tanlangan davr statistikasi' : 'Umumiy statistika (butun umr)'}
                  </p>
                  {hasStatsFilter && (
                    <button onClick={() => { setStatsFrom(''); setStatsTo('') }}
                      className="text-xs text-danger flex items-center gap-1 hover:underline">
                      <X className="w-3 h-3" /> Tozalash
                    </button>
                  )}
                </div>

                {/* Sana filtri */}
                <div className="flex gap-2 mb-4">
                  <div className="flex-1">
                    <label className="text-xs text-text-secondary mb-1 block">Dan</label>
                    <input type="date" value={statsFrom} onChange={e => setStatsFrom(e.target.value)}
                      className="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-sm" />
                  </div>
                  <div className="flex-1">
                    <label className="text-xs text-text-secondary mb-1 block">Gacha</label>
                    <input type="date" value={statsTo} onChange={e => setStatsTo(e.target.value)}
                      className="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-sm" />
                  </div>
                </div>

                {/* Raqamlar */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-2 bg-red-50 rounded-xl">
                    <p className="text-xs text-text-secondary mb-0.5">Qarz yozilgan</p>
                    <p className="font-bold text-red-600 text-sm">{formatMoney(stats?.period_debt_written ?? 0)}</p>
                  </div>
                  <div className="text-center p-2 bg-green-50 rounded-xl">
                    <p className="text-xs text-text-secondary mb-0.5">To'langan</p>
                    <p className="font-bold text-green-600 text-sm">{formatMoney(stats?.period_paid ?? 0)}</p>
                  </div>
                  <div className={cn('text-center p-2 rounded-xl',
                    (stats?.period_net ?? 0) >= 0 ? 'bg-blue-50' : 'bg-orange-50')}>
                    <p className="text-xs text-text-secondary mb-0.5">Sof</p>
                    <p className={cn('font-bold text-sm',
                      (stats?.period_net ?? 0) >= 0 ? 'text-blue-600' : 'text-orange-600')}>
                      {(stats?.period_net ?? 0) >= 0 ? '+' : ''}{formatMoney(stats?.period_net ?? 0)}
                    </p>
                  </div>
                </div>

                {/* To'lov darajasi */}
                {stats && stats.period_debt_written > 0 && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-text-secondary">To'lov darajasi</span>
                      <span className="font-semibold text-green-600">{paymentPercent}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div className="h-2 rounded-full bg-gradient-to-r from-green-400 to-green-600"
                        style={{ width: `${paymentPercent}%` }} />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Kirimlar statistika */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Kirimlar soni', value: stats?.purchase_count ?? 0, unit: 'ta', icon: ShoppingCart, color: 'text-purple-600', bg: 'bg-purple-50' },
              { label: 'Xil mahsulot', value: stats?.unique_products ?? 0, unit: 'xil', icon: Package, color: 'text-blue-600', bg: 'bg-blue-50' },
              { label: 'Jami miqdor', value: Math.round(stats?.total_items_received ?? 0), unit: 'dona', icon: BarChart3, color: 'text-cyan-600', bg: 'bg-cyan-50' },
              { label: 'Kirim summasi', value: formatMoney(stats?.total_purchase_amount ?? 0), unit: '', icon: Banknote, color: 'text-orange-600', bg: 'bg-orange-50' },
            ].map(item => (
              <Card key={item.label}>
                <CardContent className="p-3">
                  <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center mb-2', item.bg)}>
                    <item.icon className={cn('w-4 h-4', item.color)} />
                  </div>
                  <p className="text-xs text-text-secondary">{item.label}</p>
                  <p className={cn('font-bold mt-0.5', item.color)}>
                    {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
                    {item.unit && <span className="text-xs font-normal ml-1">{item.unit}</span>}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Tabs */}
          {statsLoading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-primary" /></div>
          ) : stats ? (
            <>
              <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
                {[
                  { key: 'overview', label: 'Grafik' },
                  { key: 'purchases', label: `Kirimlar (${stats.purchase_count})` },
                  { key: 'products', label: `Mahsulotlar (${stats.unique_products})` },
                ].map(tab => (
                  <button key={tab.key} onClick={() => setStatsTab(tab.key as any)}
                    className={cn('px-4 py-2 rounded-lg text-sm font-medium transition-all',
                      statsTab === tab.key ? 'bg-white shadow text-primary' : 'text-text-secondary hover:text-text-primary')}>
                    {tab.label}
                  </button>
                ))}
              </div>

              {statsTab === 'overview' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <Card className="lg:col-span-2">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="font-semibold text-sm">
                          Oylik dinamika {hasStatsFilter ? '(filtrlangan)' : '(butun umr)'}
                        </h3>
                        <div className="flex gap-3 text-xs text-text-secondary">
                          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 bg-red-400 rounded-sm inline-block" />Qarz</span>
                          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 bg-green-400 rounded-sm inline-block" />To'lov</span>
                        </div>
                      </div>
                      <BarChart data={stats.monthly} />
                      {stats.monthly.length > 0 && (
                        <div className="mt-3 pt-3 border-t grid grid-cols-2 gap-2">
                          {stats.monthly.slice(-2).reverse().map((m, i) => (
                            <div key={i} className="text-xs bg-gray-50 rounded-lg p-2">
                              <p className="font-semibold mb-1">{MONTHS_UZ[m.month - 1]} {m.year}</p>
                              <p className="text-red-600">Qarz: {formatMoney(m.debt)}</p>
                              <p className="text-green-600">To'lov: {formatMoney(m.paid)}</p>
                              <p className="text-text-secondary">{m.tx_count} ta amal</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 space-y-3">
                      <h3 className="font-semibold text-sm">Ma'lumotlar</h3>
                      {currentSupplier.phone && <div className="flex items-center gap-2 text-sm"><Phone className="w-4 h-4 text-primary" />{currentSupplier.phone}</div>}
                      {currentSupplier.contact_person && <div className="flex items-center gap-2 text-sm"><User className="w-4 h-4 text-text-secondary" />{currentSupplier.contact_person}</div>}
                      {currentSupplier.city && <div className="flex items-center gap-2 text-sm"><span>📍</span>{currentSupplier.city}</div>}
                      {currentSupplier.inn && <div className="flex items-center gap-2 text-sm"><BarChart3 className="w-4 h-4 text-text-secondary" />INN: {currentSupplier.inn}</div>}
                      {stats.last_transaction_date && (
                        <div className="border-t pt-3">
                          <p className="text-xs text-text-secondary mb-1">Oxirgi amal</p>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-3.5 h-3.5 text-text-secondary" />
                            <span className="text-sm">{formatDateTashkent(stats.last_transaction_date)}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            {stats.last_transaction_type === 'debt'
                              ? <ArrowUpRight className="w-3.5 h-3.5 text-red-500" />
                              : <ArrowDownRight className="w-3.5 h-3.5 text-green-500" />}
                            <span className={cn('text-sm font-semibold', stats.last_transaction_type === 'debt' ? 'text-red-600' : 'text-green-600')}>
                              {TX_CONF[stats.last_transaction_type as keyof typeof TX_CONF]?.label} {formatMoney(stats.last_transaction_amount || 0)}
                            </span>
                          </div>
                        </div>
                      )}
                      <div className="flex gap-0.5 pt-1">
                        {[1,2,3,4,5].map(n => <Star key={n} className={cn('w-4 h-4', n <= currentSupplier.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-200')} />)}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {statsTab === 'purchases' && (
                <Card><CardContent className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Kirimlar tarixi</h3>
                    <div className="text-sm"><span className="text-text-secondary">Jami: </span>
                      <span className="font-bold text-danger">{formatMoney(stats.total_purchase_amount)}</span></div>
                  </div>
                  {stats.purchase_docs.length === 0 ? (
                    <div className="text-center py-8 text-text-secondary">
                      <Package className="w-10 h-10 mx-auto mb-2 opacity-20" /><p>Kirimlar topilmadi</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {stats.purchase_docs.map((doc, i) => <PurchaseDocCard key={i} doc={doc} />)}
                    </div>
                  )}
                </CardContent></Card>
              )}

              {statsTab === 'products' && (
                <Card><CardContent className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Top mahsulotlar</h3>
                    <span className="text-sm text-text-secondary">Jami {stats.unique_products} xil</span>
                  </div>
                  {stats.top_products.length === 0 ? (
                    <div className="text-center py-8 text-text-secondary">
                      <Package className="w-10 h-10 mx-auto mb-2 opacity-20" /><p>Mahsulotlar topilmadi</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead><tr className="border-b bg-gray-50">
                          <th className="text-left px-4 py-2.5 font-medium text-text-secondary">#</th>
                          <th className="text-left px-4 py-2.5 font-medium text-text-secondary">Mahsulot</th>
                          <th className="text-right px-4 py-2.5 font-medium text-text-secondary">Miqdor</th>
                          <th className="text-right px-4 py-2.5 font-medium text-text-secondary">Buyurtma</th>
                          <th className="text-right px-4 py-2.5 font-medium text-text-secondary">Jami summa</th>
                        </tr></thead>
                        <tbody>
                          {stats.top_products.map((p, i) => (
                            <tr key={p.product_id} className={cn('border-b border-gray-50', i % 2 === 1 ? 'bg-gray-50/50' : '')}>
                              <td className="px-4 py-3 text-text-secondary">{i + 1}</td>
                              <td className="px-4 py-3 font-medium">{p.product_name}</td>
                              <td className="px-4 py-3 text-right">{p.total_quantity} {p.uom_symbol}</td>
                              <td className="px-4 py-3 text-right text-text-secondary">{p.times_ordered} marta</td>
                              <td className="px-4 py-3 text-right font-semibold text-danger">{formatMoney(p.total_amount)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent></Card>
              )}
            </>
          ) : statsError ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-600">
              Statistika yuklanmadi. Server xatosi ro'y berdi.
            </div>
          ) : null}

          {/* Tranzaksiyalar */}
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="font-semibold">Tranzaksiyalar tarixi</h2>
            <div className="flex flex-wrap gap-2 ml-auto items-center">
              <select value={txType} onChange={e => setTxType(e.target.value)}
                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white">
                <option value="">Barcha tur</option>
                <option value="debt">Qarz</option>
                <option value="payment">To'lov</option>
                <option value="return">Qaytarish</option>
              </select>
              <input type="date" value={txFrom} onChange={e => setTxFrom(e.target.value)}
                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm" />
              <input type="date" value={txTo} onChange={e => setTxTo(e.target.value)}
                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm" />
              <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                <input type="checkbox" checked={showDeletedTx} onChange={e => setShowDeletedTx(e.target.checked)} className="w-4 h-4 rounded" />
                O'chirilganlar
              </label>
              {(txType || txFrom || txTo) && (
                <button onClick={() => { setTxType(''); setTxFrom(''); setTxTo('') }}
                  className="flex items-center gap-1 text-xs text-danger"><X className="w-3 h-3" /> Tozalash</button>
              )}
            </div>
          </div>

          <Card><CardContent className="p-0">
            {txLoading ? (
              <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-primary" /></div>
            ) : transactions.length === 0 ? (
              <div className="flex flex-col items-center py-12 text-text-secondary">
                <History className="w-10 h-10 mb-2 opacity-20" /><p>Tranzaksiyalar yo'q</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {transactions.map(tx => {
                  const cfg = TX_CONF[tx.transaction_type]
                  return (
                    <div key={tx.id} className={cn('p-4 flex gap-3 items-start',
                      tx.is_deleted ? 'bg-red-50/30 opacity-60' : 'hover:bg-gray-50/50')}>
                      <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0',
                        tx.transaction_type === 'debt' ? 'bg-red-100' :
                        tx.transaction_type === 'payment' ? 'bg-green-100' : 'bg-blue-100')}>
                        <cfg.icon className={cn('w-5 h-5',
                          tx.transaction_type === 'debt' ? 'text-red-600' :
                          tx.transaction_type === 'payment' ? 'text-green-600' : 'text-blue-600')} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 justify-between">
                          <div className="flex items-center gap-2">
                            <span className={cn('px-2 py-0.5 rounded-full text-xs font-semibold', cfg.color)}>{cfg.label}</span>
                            <span className="font-bold">{tx.currency === 'usd' ? `$${Number(tx.amount).toFixed(2)}` : formatMoney(tx.amount)}</span>
                            {tx.currency === 'usd' && tx.amount_uzs && (
                              <span className="text-xs text-text-secondary">≈ {formatMoney(tx.amount_uzs)}</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-text-secondary">{formatDateTashkent(tx.transaction_date)}</span>
                            {!tx.is_deleted && (
                              <button onClick={() => { setDeletingTx(tx); setShowDeleteTx(true) }}
                                className="p-1.5 rounded-lg hover:bg-red-50 text-text-secondary hover:text-danger">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-text-secondary mt-1.5 bg-gray-50 rounded-lg px-3 py-1.5 italic">"{tx.comment}"</p>
                        <div className="flex gap-4 mt-1.5 text-xs text-text-secondary">
                          <span>{tx.created_by_name}</span><span>{formatDateTimeTashkent(tx.created_at)}</span>
                        </div>
                        {tx.is_deleted && (
                          <div className="mt-2 bg-red-50 border border-red-100 rounded-lg px-3 py-2 text-xs">
                            <p className="font-semibold text-red-600">O'chirilgan — {tx.deleted_by_name}</p>
                            {tx.delete_comment && <p className="text-red-500">Sabab: {tx.delete_comment}</p>}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent></Card>
        </div>
      )}

      {/* ═══ MODALS ═══ */}
      <SupplierFormModal open={showForm} onClose={() => setShowForm(false)} supplier={editingSupplier}
        onSaved={(s) => {
          qc.invalidateQueries({ queryKey: ['suppliers'] })
          qc.invalidateQueries({ queryKey: ['supplier-detail', s.id] })
          setShowForm(false)
          if (view === 'detail') { setSelected(s); refetchDetail() }
        }} />

      {selected && (
        <TxFormModal open={showTxModal} onClose={() => setShowTxModal(false)}
          supplierId={selected.id} defaultType={txDefaultType} onSaved={handleTxSaved}
          currentDebt={stats?.current_debt ?? currentSupplier?.current_debt}
          currentAdvance={stats?.current_advance ?? currentSupplier?.advance_balance} />
      )}

      <Dialog open={showDeleteSupplier} onOpenChange={setShowDeleteSupplier}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle className="flex items-center gap-2 text-danger"><AlertTriangle className="w-5 h-5" /> O'chirishni tasdiqlang</DialogTitle></DialogHeader>
          <div className="py-3 text-sm text-text-secondary">
            <strong className="text-text-primary">{selected?.name}</strong> ta'minotchisini o'chirmoqchimisiz?
            {selected && selected.current_debt > 0 && (
              <p className="mt-2 text-danger font-medium">⚠️ Qarz: {formatMoney(selected.current_debt)} — avval to'lang!</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteSupplier(false)}>Bekor</Button>
            <Button variant="destructive" onClick={() => selected && deleteSupplier.mutate(selected.id)} disabled={deleteSupplier.isPending}>O'chirish</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showDeleteTx} onOpenChange={setShowDeleteTx}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle className="flex items-center gap-2 text-danger"><AlertTriangle className="w-5 h-5" /> Tranzaksiyani o'chirish</DialogTitle></DialogHeader>
          {deletingTx && (
            <div className="py-2 space-y-3">
              <div className="bg-gray-50 rounded-xl p-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className={cn('px-2 py-0.5 rounded-full text-xs font-semibold', TX_CONF[deletingTx.transaction_type].color)}>
                    {TX_CONF[deletingTx.transaction_type].label}
                  </span>
                  <span className="font-bold">{formatMoney(deletingTx.amount_uzs || deletingTx.amount)}</span>
                </div>
                <p className="text-text-secondary mt-2 italic">"{deletingTx.comment}"</p>
              </div>
              <p className="text-sm text-text-secondary">O'chirilganda balans avtomatik qayta hisoblanadi. Tarix saqlanib qoladi.</p>
              <div className="bg-red-50 border border-red-200 rounded-xl p-3">
                <label className="text-sm font-medium mb-1.5 block text-red-800">O'chirish sababi * <span className="font-normal text-red-500">(majburiy)</span></label>
                <textarea value={deleteTxComment} onChange={e => setDeleteTxComment(e.target.value)}
                  placeholder="Nima uchun o'chirilmoqda?" rows={3}
                  className="w-full px-3 py-2 border border-red-200 rounded-lg text-sm bg-white resize-none" />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowDeleteTx(false); setDeleteTxComment(''); setDeletingTx(null) }}>Bekor</Button>
            <Button variant="destructive"
              onClick={() => { if (deleteTxComment.trim().length < 3) { toast.error('Izoh kiriting'); return } deleteTxMut.mutate({ id: deletingTx!.id, comment: deleteTxComment }) }}
              disabled={deleteTxMut.isPending}>
              {deleteTxMut.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />} O'chirish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
