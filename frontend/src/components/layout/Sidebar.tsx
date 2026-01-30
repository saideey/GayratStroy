import { useState, useEffect, useRef } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Users,
  Warehouse,
  FileText,
  Settings,
  LogOut,
  HelpCircle,
  X,
  Instagram,
  Send,
  UsersRound,
  Key,
  Receipt,
  ChevronDown,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'
import { useLanguage } from '@/contexts/LanguageContext'
import api from '@/services/api'

interface NavItem {
  nameKey: 'dashboard' | 'pos' | 'sales' | 'products' | 'customers' | 'warehouse' | 'reports' | 'users' | 'settings'
  href: string
  icon: React.ElementType
  permission?: string
}

const navItems: NavItem[] = [
  { nameKey: 'dashboard', href: '/', icon: LayoutDashboard },
  { nameKey: 'pos', href: '/pos', icon: ShoppingCart },
  { nameKey: 'sales', href: '/sales', icon: Receipt },
  { nameKey: 'products', href: '/products', icon: Package },
  { nameKey: 'customers', href: '/customers', icon: Users },
  { nameKey: 'warehouse', href: '/warehouse', icon: Warehouse },
  { nameKey: 'reports', href: '/reports', icon: FileText, permission: 'REPORT_SALES' },
  { nameKey: 'users', href: '/users', icon: UsersRound, permission: 'USER_VIEW' },
  { nameKey: 'settings', href: '/settings', icon: Settings, permission: 'SETTINGS_VIEW' },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation()
  const { user, logout, hasPermission } = useAuthStore()
  const { t } = useLanguage()
  const [showHelp, setShowHelp] = useState(false)
  const [showChangePassword, setShowChangePassword] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [passwordData, setPasswordData] = useState({ current: '', new: '', confirm: '' })
  const [showPasswords, setShowPasswords] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  const handleChangePassword = async () => {
    if (!passwordData.current || !passwordData.new || !passwordData.confirm) {
      alert(t('required'))
      return
    }
    if (passwordData.new !== passwordData.confirm) {
      alert(t('passwordMismatch'))
      return
    }
    if (passwordData.new.length < 6) {
      alert(t('minLength').replace('{min}', '6'))
      return
    }

    setChangingPassword(true)
    try {
      const response = await api.post('/users/change-password', {
        current_password: passwordData.current,
        new_password: passwordData.new
      })

      if (response.data) {
        alert(t('passwordChanged'))
        setShowChangePassword(false)
        setPasswordData({ current: '', new: '', confirm: '' })
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || t('errorOccurred'))
    } finally {
      setChangingPassword(false)
    }
  }

  const filteredNavItems = navItems.filter(
    (item) => !item.permission || hasPermission(item.permission)
  )

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 h-screen w-72 bg-surface border-r border-border flex flex-col z-50',
          'transition-transform duration-300 ease-in-out',
          'lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="p-5 lg:p-6 border-b border-border flex items-center justify-between">
          <img
            src="/logo.png"
            alt="G'ayrat Stroy House"
            className="h-16 lg:h-20 xl:h-24 w-auto object-contain"
          />
          {/* Close button for mobile */}
          <button
            onClick={onClose}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 lg:p-4 space-y-1 lg:space-y-2 overflow-y-auto">
          {filteredNavItems.map((item) => {
            const isActive = location.pathname === item.href ||
              (item.href !== '/' && location.pathname.startsWith(item.href))

            return (
              <NavLink
                key={item.href}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 lg:gap-4 px-3 lg:px-4 py-3 lg:py-4 rounded-xl font-medium transition-all',
                  'text-base hover:bg-gray-100 active:scale-[0.98]',
                  isActive && 'bg-primary text-white hover:bg-primary-dark'
                )}
              >
                <item.icon className="h-5 w-5 lg:h-6 lg:w-6 min-h-5 min-w-5 lg:min-h-6 lg:min-w-6 flex-shrink-0" />
                <span className="truncate">{t(item.nameKey)}</span>
              </NavLink>
            )
          })}
        </nav>

        {/* Help Button */}
        <div className="px-3 lg:px-4 py-2 border-t border-border">
          <button
            onClick={() => setShowHelp(true)}
            className="flex items-center gap-3 lg:gap-4 w-full px-3 lg:px-4 py-3 rounded-xl font-medium hover:bg-gray-100 transition-colors text-text-secondary"
          >
            <HelpCircle className="h-5 w-5 lg:h-6 lg:w-6 flex-shrink-0" />
            <span>{t('help')}</span>
          </button>
        </div>

        {/* User Info with Dropdown */}
        <div className="p-3 lg:p-4 border-t border-border relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center justify-between w-full px-3 lg:px-4 py-2.5 lg:py-3 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <div className="flex-1 text-left min-w-0">
              <p className="font-semibold text-text-primary truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-sm text-text-secondary truncate">
                {user?.role_name}
              </p>
            </div>
            <ChevronDown className={cn(
              "w-5 h-5 text-text-secondary transition-transform flex-shrink-0 ml-2",
              showUserMenu && "rotate-180"
            )} />
          </button>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <div className="absolute bottom-full left-3 right-3 mb-2 bg-white rounded-xl shadow-lg border border-border overflow-hidden z-10">
              <button
                onClick={() => {
                  setShowChangePassword(true)
                  setShowUserMenu(false)
                }}
                className="flex items-center gap-3 w-full px-4 py-3 hover:bg-yellow-50 text-yellow-600 transition-colors border-b border-border"
              >
                <Key className="h-5 w-5 flex-shrink-0" />
                <span className="font-medium">{t('changePassword')}</span>
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-4 py-3 hover:bg-danger/10 text-danger transition-colors"
              >
                <LogOut className="h-5 w-5 flex-shrink-0" />
                <span className="font-medium">{t('logout')}</span>
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-5 lg:p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl lg:text-2xl font-bold">XLAB</h2>
                  <p className="text-blue-100 text-sm">IT Solutions & Development</p>
                </div>
                <button
                  onClick={() => setShowHelp(false)}
                  className="p-2 hover:bg-white/20 rounded-full transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-5 lg:p-6 space-y-4">
              <p className="text-gray-600 text-center text-sm lg:text-base">
                {t('helpText')}
              </p>

              {/* Contact Links */}
              <div className="space-y-3">
                <a
                  href="https://www.instagram.com/xlabuz/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 lg:gap-4 p-3 lg:p-4 bg-gradient-to-r from-pink-500 to-purple-500 text-white rounded-xl hover:opacity-90 transition-opacity active:scale-[0.98]"
                >
                  <div className="p-2 bg-white/20 rounded-lg">
                    <Instagram className="w-5 h-5 lg:w-6 lg:h-6" />
                  </div>
                  <div>
                    <p className="font-semibold">Instagram</p>
                    <p className="text-sm text-white/80">@xlabuz</p>
                  </div>
                </a>

                <a
                  href="https://t.me/xlab_uz"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 lg:gap-4 p-3 lg:p-4 bg-gradient-to-r from-blue-400 to-blue-600 text-white rounded-xl hover:opacity-90 transition-opacity active:scale-[0.98]"
                >
                  <div className="p-2 bg-white/20 rounded-lg">
                    <Send className="w-5 h-5 lg:w-6 lg:h-6" />
                  </div>
                  <div>
                    <p className="font-semibold">Telegram</p>
                    <p className="text-sm text-white/80">@xlab_uz</p>
                  </div>
                </a>
              </div>

              {/* Footer */}
              <div className="pt-4 border-t border-gray-100 text-center">
                <p className="text-xs text-gray-400">
                  © 2026 XLAB. {t('allRightsReserved')}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showChangePassword && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-yellow-500 to-orange-500 p-5 lg:p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg lg:text-xl font-bold">{t('changePassword')}</h2>
                  <p className="text-yellow-100 text-sm">
                    {t('updatePasswordHint')}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowChangePassword(false)
                    setPasswordData({ current: '', new: '', confirm: '' })
                  }}
                  className="p-2 hover:bg-white/20 rounded-full transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Form */}
            <div className="p-5 lg:p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">{t('currentPassword')}</label>
                <input
                  type={showPasswords ? 'text' : 'password'}
                  value={passwordData.current}
                  onChange={(e) => setPasswordData({ ...passwordData, current: e.target.value })}
                  placeholder={t('currentPassword')}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-yellow-500/20 focus:border-yellow-500 text-base"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">{t('newPassword')}</label>
                <input
                  type={showPasswords ? 'text' : 'password'}
                  value={passwordData.new}
                  onChange={(e) => setPasswordData({ ...passwordData, new: e.target.value })}
                  placeholder={t('minLength').replace('{min}', '6')}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-yellow-500/20 focus:border-yellow-500 text-base"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">{t('confirmPassword')}</label>
                <input
                  type={showPasswords ? 'text' : 'password'}
                  value={passwordData.confirm}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm: e.target.value })}
                  placeholder={t('confirmPassword')}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-yellow-500/20 focus:border-yellow-500 text-base"
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showPasswords}
                  onChange={(e) => setShowPasswords(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300"
                />
                <span className="text-sm text-gray-600">
                  {t('showPasswords')}
                </span>
              </label>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowChangePassword(false)
                    setPasswordData({ current: '', new: '', confirm: '' })
                  }}
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl hover:bg-gray-50 font-medium transition-colors active:scale-[0.98]"
                >
                  {t('cancel')}
                </button>
                <button
                  onClick={handleChangePassword}
                  disabled={changingPassword}
                  className="flex-1 px-4 py-3 bg-yellow-500 text-white rounded-xl hover:bg-yellow-600 font-medium transition-colors disabled:opacity-50 active:scale-[0.98]"
                >
                  {changingPassword ? t('loading') : t('save')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}