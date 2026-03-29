import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import {
  ShoppingCart, TrendingUp, TrendingDown, Users, Package,
  AlertTriangle, ArrowRight, Building2, Wallet, BarChart3,
  CreditCard, Banknote, Smartphone, RefreshCw, Loader2,
  ArrowUpRight, ArrowDownRight, Star
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui'
import api from '@/services/api'
import { formatMoney, cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'

// ─── Types ────────────────────────────────────────────────────────────────────
interface DashboardData {
  today: {
    date: string; sales_count: number; revenue: number; paid: number
    debt_added: number; expenses: number; profit: number
    yesterday_revenue: number; change_percent: number
    payment_methods: { cash: number; card: number; transfer: number; other: number }
  }
  month: { label: string; sales_count: number; revenue: number; expenses: number; profit: number }
  daily_chart: { date: string; day_name: string; day: string; revenue: number; count: number }[]
  top_products: { name: string; qty: number; revenue: number }[]
  seller_stats: { name: string; count: number; revenue: number }[]
  customers: { total_debt: number; debtors_count: number; top_debtors: { id: number; name: string; phone: string; debt: number }[] }
  suppliers: { total_debt: number; debtors_count: number; top_debtors: { id: number; name: string; debt: number }[] }
  warehouse: { total_value: number; total_products: number; low_stock_count: number; low_stock_items: { product_id: number; product_name: string; current_stock: number; min_stock: number; uom: string }[] }
}

// ─── Mini bar chart ───────────────────────────────────────────────────────────
function MiniChart({ data }: { data: DashboardData['daily_chart'] }) {
  const max = Math.max(...data.map(d => d.revenue), 1)
  const today = new Date().toISOString().split('T')[0]
  return (
    <div className="flex items-end gap-1 h-16 mt-1">
      {data.map((d, i) => {
        const isToday = d.date === today
        const h = Math.max(4, (d.revenue / max) * 56)
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div className="relative w-full flex items-end justify-center" style={{ height: 56 }}>
              {d.revenue > 0 && (
                <div
                  className={cn('w-full rounded-t-sm transition-all', isToday ? 'bg-primary' : 'bg-primary/30 hover:bg-primary/50')}
                  style={{ height: h }}
                  title={`${d.day}: ${formatMoney(d.revenue)}`}
                />
              )}
            </div>
            <span className={cn('text-[9px] font-medium', isToday ? 'text-primary' : 'text-text-secondary')}>{d.day_name}</span>
          </div>
        )
      })}
    </div>
  )
}

// ─── Stat card ────────────────────────────────────────────────────────────────
function StatCard({ title, value, sub, icon: Icon, iconBg, iconColor, trend, link }: {
  title: string; value: string; sub?: string; icon: any; iconBg: string; iconColor: string
  trend?: { value: number; label: string }; link?: string
}) {
  const navigate = useNavigate()
  return (
    <Card className={cn('cursor-pointer hover:shadow-md transition-shadow', link && 'cursor-pointer')}
      onClick={() => link && navigate(link)}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', iconBg)}>
            <Icon className={cn('w-5 h-5', iconColor)} />
          </div>
          {trend && (
            <div className={cn('flex items-center gap-0.5 text-xs font-medium',
              trend.value >= 0 ? 'text-green-600' : 'text-red-500')}>
              {trend.value >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
              {Math.abs(trend.value)}%
            </div>
          )}
        </div>
        <div className="mt-3">
          <p className="text-2xl font-bold text-text-primary leading-tight">{value}</p>
          <p className="text-xs text-text-secondary mt-0.5">{title}</p>
          {sub && <p className="text-xs text-text-secondary mt-0.5 font-medium">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Section header ───────────────────────────────────────────────────────────
function SectionHeader({ title, linkTo, icon: Icon, iconColor }: {
  title: string; linkTo: string; icon: any; iconColor: string
}) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <Icon className={cn('w-4 h-4', iconColor)} />
        {title}
      </h3>
      <Link to={linkTo} className="text-xs text-primary flex items-center gap-0.5 hover:underline">
        Barchasi <ArrowRight className="w-3 h-3" />
      </Link>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { user } = useAuthStore()
  const isDirector = user?.role_type === 'DIRECTOR' || user?.role_type === 'director'

  const { data: rawData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: async () => (await api.get('/dashboard')).data.data as DashboardData,
    refetchInterval: 60_000, // 1 daqiqada yangilanadi
    staleTime: 30_000,
  })

  const d = rawData

  const DAYS_UZ = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
  const MONTHS_UZ = ['Yanvar','Fevral','Mart','Aprel','May','Iyun','Iyul','Avgust','Sentyabr','Oktyabr','Noyabr','Dekabr']
  const today = new Date()
  const dateStr = `${DAYS_UZ[today.getDay() === 0 ? 6 : today.getDay() - 1]}, ${today.getDate()} ${MONTHS_UZ[today.getMonth()]} ${today.getFullYear()}`

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-5">

      {/* ── Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Boshqaruv paneli</h1>
          <p className="text-sm text-text-secondary mt-0.5">{dateStr}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => refetch()} disabled={isFetching}
            className="p-2 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors">
            <RefreshCw className={cn('w-4 h-4 text-text-secondary', isFetching && 'animate-spin')} />
          </button>
          <Link to="/pos">
            <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-colors text-sm">
              <ShoppingCart className="w-4 h-4" /> Sotuv (POS)
            </button>
          </Link>
        </div>
      </div>

      {/* ── Bugungi asosiy kartochkalar ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          title="Bugungi sotuv"
          value={formatMoney(d?.today.revenue ?? 0)}
          sub={`${d?.today.sales_count ?? 0} ta chek`}
          icon={ShoppingCart}
          iconBg="bg-primary/10" iconColor="text-primary"
          trend={{ value: d?.today.change_percent ?? 0, label: "kecha nisbatan" }}
          link="/sales"
        />
        <StatCard
          title="To'langan (bugun)"
          value={formatMoney(d?.today.paid ?? 0)}
          sub={`Qarz: ${formatMoney(d?.today.debt_added ?? 0)}`}
          icon={CreditCard}
          iconBg="bg-green-100" iconColor="text-green-600"
          link="/sales"
        />
        <StatCard
          title="Chiqimlar (bugun)"
          value={formatMoney(d?.today.expenses ?? 0)}
          sub={`Sof foyda: ${formatMoney(d?.today.profit ?? 0)}`}
          icon={Wallet}
          iconBg="bg-orange-100" iconColor="text-orange-600"
          link="/expenses"
        />
        <StatCard
          title="Oylik daromad"
          value={formatMoney(d?.month.revenue ?? 0)}
          sub={`${d?.month.sales_count ?? 0} ta sotuv`}
          icon={TrendingUp}
          iconBg="bg-purple-100" iconColor="text-purple-600"
          link="/reports"
        />
      </div>

      {/* ── 7 kunlik grafik + to'lov usullari ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Grafik */}
        <Card className="lg:col-span-2">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-semibold text-sm">So'nggi 7 kun</h3>
              <div className="flex items-center gap-3 text-xs text-text-secondary">
                <span>Bugun: <span className="font-bold text-primary">{formatMoney(d?.today.revenue ?? 0)}</span></span>
                <span>Kecha: <span className="font-medium">{formatMoney(d?.today.yesterday_revenue ?? 0)}</span></span>
              </div>
            </div>
            {d?.daily_chart && <MiniChart data={d.daily_chart} />}
            {/* Oxirgi 2 kunning raqamlari */}
            <div className="grid grid-cols-7 gap-1 mt-2">
              {d?.daily_chart.map((day, i) => (
                <div key={i} className="text-center">
                  {day.count > 0 && (
                    <p className="text-[9px] text-text-secondary">{day.count} ta</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* To'lov usullari */}
        <Card>
          <CardContent className="p-4">
            <h3 className="font-semibold text-sm mb-3">To'lov usullari (bugun)</h3>
            <div className="space-y-2">
              {[
                { key: 'cash', label: 'Naqd', icon: Banknote, color: 'text-green-600', bg: 'bg-green-50' },
                { key: 'card', label: 'Karta', icon: CreditCard, color: 'text-blue-600', bg: 'bg-blue-50' },
                { key: 'transfer', label: 'O\'tkazma', icon: Smartphone, color: 'text-purple-600', bg: 'bg-purple-50' },
                { key: 'other', label: 'Boshqa', icon: Wallet, color: 'text-gray-500', bg: 'bg-gray-50' },
              ].map(m => {
                const val = (d?.today.payment_methods as any)?.[m.key] ?? 0
                const total = d?.today.revenue ?? 1
                const pct = total > 0 ? Math.round((val / total) * 100) : 0
                return (
                  <div key={m.key} className="flex items-center gap-2">
                    <div className={cn('w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0', m.bg)}>
                      <m.icon className={cn('w-3.5 h-3.5', m.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between text-xs mb-0.5">
                        <span className="text-text-secondary">{m.label}</span>
                        <span className="font-medium">{formatMoney(val)}</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-1.5">
                        <div className={cn('h-1.5 rounded-full', m.color.replace('text-', 'bg-'))}
                          style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                    <span className="text-xs text-text-secondary w-8 text-right">{pct}%</span>
                  </div>
                )
              })}
            </div>

            {/* Oylik xulosa */}
            <div className="mt-4 pt-4 border-t space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-text-secondary">Oylik daromad</span>
                <span className="font-semibold text-primary">{formatMoney(d?.month.revenue ?? 0)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-secondary">Oylik chiqim</span>
                <span className="font-semibold text-orange-600">{formatMoney(d?.month.expenses ?? 0)}</span>
              </div>
              <div className="flex justify-between text-xs pt-1 border-t">
                <span className="font-medium">Oylik sof foyda</span>
                <span className={cn('font-bold', (d?.month.profit ?? 0) >= 0 ? 'text-green-600' : 'text-red-600')}>
                  {formatMoney(d?.month.profit ?? 0)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Mijoz + Ta'minotchi qarzdorlar ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Mijoz qarzdorlar */}
        <Card>
          <CardContent className="p-4">
            <SectionHeader title="Mijoz qarzdorlar" linkTo="/customers" icon={Users} iconColor="text-red-500" />

            {/* Umumiy */}
            <div className="flex items-center justify-between bg-red-50 rounded-xl px-4 py-2.5 mb-3">
              <div>
                <p className="text-xs text-text-secondary">Umumiy qarz</p>
                <p className="font-bold text-red-600">{formatMoney(d?.customers.total_debt ?? 0)}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary">Qarzdorlar</p>
                <p className="font-bold text-red-600">{d?.customers.debtors_count ?? 0} ta</p>
              </div>
            </div>

            {/* Ro'yxat */}
            {(d?.customers.top_debtors ?? []).length === 0 ? (
              <div className="text-center py-6 text-text-secondary text-sm">
                <Users className="w-8 h-8 mx-auto mb-2 opacity-20" />
                Qarzdorlar yo'q ✓
              </div>
            ) : (
              <div className="space-y-1.5">
                {(d?.customers.top_debtors ?? []).map((c, i) => (
                  <Link to="/customers" key={c.id}>
                    <div className="flex items-center justify-between p-2.5 rounded-xl hover:bg-gray-50 transition-colors">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="w-5 h-5 bg-red-100 text-red-600 rounded-full text-xs flex items-center justify-center font-bold flex-shrink-0">{i+1}</span>
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{c.name}</p>
                          {c.phone && <p className="text-xs text-text-secondary">{c.phone}</p>}
                        </div>
                      </div>
                      <span className="text-sm font-bold text-red-600 flex-shrink-0 ml-2">{formatMoney(c.debt)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Ta'minotchi qarzdorlar */}
        <Card>
          <CardContent className="p-4">
            <SectionHeader title="Ta'minotchilarga qarz" linkTo="/suppliers" icon={Building2} iconColor="text-orange-500" />

            {/* Umumiy */}
            <div className="flex items-center justify-between bg-orange-50 rounded-xl px-4 py-2.5 mb-3">
              <div>
                <p className="text-xs text-text-secondary">Biz ularga qarzlimiz</p>
                <p className="font-bold text-orange-600">{formatMoney(d?.suppliers.total_debt ?? 0)}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary">Ta'minotchilar</p>
                <p className="font-bold text-orange-600">{d?.suppliers.debtors_count ?? 0} ta</p>
              </div>
            </div>

            {/* Ro'yxat */}
            {(d?.suppliers.top_debtors ?? []).length === 0 ? (
              <div className="text-center py-6 text-text-secondary text-sm">
                <Building2 className="w-8 h-8 mx-auto mb-2 opacity-20" />
                Qarz yo'q ✓
              </div>
            ) : (
              <div className="space-y-1.5">
                {(d?.suppliers.top_debtors ?? []).map((s, i) => (
                  <Link to="/suppliers" key={s.id}>
                    <div className="flex items-center justify-between p-2.5 rounded-xl hover:bg-gray-50 transition-colors">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="w-5 h-5 bg-orange-100 text-orange-600 rounded-full text-xs flex items-center justify-center font-bold flex-shrink-0">{i+1}</span>
                        <p className="text-sm font-medium truncate">{s.name}</p>
                      </div>
                      <span className="text-sm font-bold text-orange-600 flex-shrink-0 ml-2">{formatMoney(s.debt)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Ombor + Top mahsulotlar ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Kam qoldiq */}
        <Card>
          <CardContent className="p-4">
            <SectionHeader title="Kam qoldiqli tovarlar" linkTo="/warehouse" icon={AlertTriangle} iconColor="text-yellow-500" />

            <div className="flex items-center justify-between bg-yellow-50 rounded-xl px-4 py-2.5 mb-3">
              <div>
                <p className="text-xs text-text-secondary">Ombor qiymati</p>
                <p className="font-bold text-text-primary">{formatMoney(d?.warehouse.total_value ?? 0)}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-secondary">Mahsulotlar</p>
                <p className="font-bold">{d?.warehouse.total_products ?? 0} ta</p>
              </div>
            </div>

            {(d?.warehouse.low_stock_items ?? []).length === 0 ? (
              <div className="text-center py-6 text-text-secondary text-sm">
                <Package className="w-8 h-8 mx-auto mb-2 opacity-20" />
                Barcha tovarlar yetarli ✓
              </div>
            ) : (
              <div className="space-y-1.5">
                {(d?.warehouse.low_stock_items ?? []).map((item, i) => (
                  <Link to="/warehouse" key={item.product_id}>
                    <div className={cn('flex items-center justify-between p-2.5 rounded-xl hover:bg-gray-50',
                      item.current_stock === 0 ? 'bg-red-50' : 'bg-yellow-50/50')}>
                      <div className="flex items-center gap-2 min-w-0">
                        <Package className={cn('w-3.5 h-3.5 flex-shrink-0', item.current_stock === 0 ? 'text-red-500' : 'text-yellow-500')} />
                        <p className="text-sm font-medium truncate">{item.product_name}</p>
                      </div>
                      <div className="text-right flex-shrink-0 ml-2">
                        <span className={cn('text-xs font-bold', item.current_stock === 0 ? 'text-red-600' : 'text-yellow-600')}>
                          {item.current_stock} {item.uom}
                        </span>
                        <p className="text-[10px] text-text-secondary">min: {item.min_stock}</p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top mahsulotlar + Sotuvchilar */}
        <div className="space-y-4">
          <Card>
            <CardContent className="p-4">
              <SectionHeader title="Top mahsulotlar (oy)" linkTo="/reports" icon={BarChart3} iconColor="text-blue-500" />
              {(d?.top_products ?? []).length === 0 ? (
                <p className="text-center py-4 text-sm text-text-secondary">Ma'lumot yo'q</p>
              ) : (
                <div className="space-y-2">
                  {(d?.top_products ?? []).map((p, i) => {
                    const maxRev = Math.max(...(d?.top_products ?? []).map(x => x.revenue), 1)
                    const pct = Math.round((p.revenue / maxRev) * 100)
                    return (
                      <div key={i} className="flex items-center gap-2">
                        <span className="w-5 text-xs text-text-secondary font-medium text-right flex-shrink-0">{i+1}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between text-xs mb-0.5">
                            <span className="font-medium truncate">{p.name}</span>
                            <span className="text-text-secondary flex-shrink-0 ml-1">{formatMoney(p.revenue)}</span>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-1.5">
                            <div className="h-1.5 rounded-full bg-blue-400" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sotuvchilar — faqat director */}
          {isDirector && (
            <Card>
              <CardContent className="p-4">
                <SectionHeader title="Sotuvchilar (bugun)" linkTo="/reports" icon={Star} iconColor="text-yellow-500" />
                {(d?.seller_stats ?? []).length === 0 ? (
                  <p className="text-center py-4 text-sm text-text-secondary">Bugun sotuv yo'q</p>
                ) : (
                  <div className="space-y-1.5">
                    {(d?.seller_stats ?? []).map((s, i) => (
                      <div key={i} className="flex items-center justify-between p-2 rounded-xl hover:bg-gray-50">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 bg-yellow-100 text-yellow-600 rounded-full text-xs flex items-center justify-center font-bold">{i+1}</span>
                          <p className="text-sm font-medium">{s.name}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold text-primary">{formatMoney(s.revenue)}</p>
                          <p className="text-[10px] text-text-secondary">{s.count} ta chek</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* ── Tezkor havolalar ── */}
      <Card>
        <CardContent className="p-4">
          <h3 className="font-semibold text-sm mb-3">Tezkor o'tish</h3>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {[
              { to: '/pos', icon: ShoppingCart, label: 'Sotuv', color: 'text-primary', bg: 'bg-primary/10' },
              { to: '/sales', icon: TrendingUp, label: 'Sotuvlar', color: 'text-green-600', bg: 'bg-green-100' },
              { to: '/customers', icon: Users, label: 'Mijozlar', color: 'text-blue-600', bg: 'bg-blue-100' },
              { to: '/warehouse', icon: Package, label: 'Ombor', color: 'text-yellow-600', bg: 'bg-yellow-100' },
              { to: '/suppliers', icon: Building2, label: "Ta'minotchi", color: 'text-orange-600', bg: 'bg-orange-100' },
              { to: '/expenses', icon: Wallet, label: 'Chiqimlar', color: 'text-red-500', bg: 'bg-red-100' },
            ].map(item => (
              <Link to={item.to} key={item.to}>
                <div className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-gray-50 transition-colors">
                  <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', item.bg)}>
                    <item.icon className={cn('w-5 h-5', item.color)} />
                  </div>
                  <span className="text-xs font-medium text-text-secondary text-center leading-tight">{item.label}</span>
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
