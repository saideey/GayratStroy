import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import {
  Users as UsersIcon,
  Plus,
  Search,
  Edit,
  Trash2,
  Key,
  Loader2,
  Shield,
  UserCheck,
  UserX,
  Eye,
  EyeOff,
  X,
  Phone,
  Mail,
  Calendar,
  Clock
} from 'lucide-react'
import toast from 'react-hot-toast'
import { Button, Input, Card, CardContent, Badge } from '@/components/ui'
import usersService, { User, Role, CreateUserData, UpdateUserData } from '@/services/usersService'
import { formatDateTimeTashkent } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'
import { useLanguage } from '@/contexts/LanguageContext'

export default function UsersPage() {
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuthStore()
  const { t } = useLanguage()
  const [search, setSearch] = useState('')
  const [filterRole, setFilterRole] = useState<number | ''>('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  
  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  // Fetch users
  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users', search, filterRole, filterStatus],
    queryFn: () => usersService.getUsers({
      search: search || undefined,
      role_id: filterRole || undefined,
      is_active: filterStatus === '' ? undefined : filterStatus === 'active'
    })
  })

  // Fetch roles
  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: usersService.getRoles
  })

  const users: User[] = usersData?.data || []
  const roles: Role[] = rolesData?.data || []

  // Create user form
  const createForm = useForm<CreateUserData>({
    defaultValues: {
      username: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      email: '',
      role_id: 0
    }
  })

  // Edit user form
  const editForm = useForm<UpdateUserData>()

  // Reset password form
  const resetPasswordForm = useForm<{ new_password: string; confirm_password: string }>()

  // Create user mutation
  const createUserMutation = useMutation({
    mutationFn: usersService.createUser,
    onSuccess: () => {
      toast.success(t('savedSuccess'))
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowCreateModal(false)
      createForm.reset()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        // Pydantic validation error
        const messages = detail.map((err: any) => err.msg || err.message).join(', ')
        toast.error(messages || t('errorOccurred'))
      } else if (typeof detail === 'string') {
        toast.error(detail)
      } else {
        toast.error(t('errorOccurred'))
      }
    }
  })

  // Update user mutation
  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserData }) => 
      usersService.updateUser(id, data),
    onSuccess: () => {
      toast.success(t('updatedSuccess'))
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowEditModal(false)
      setSelectedUser(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || t('errorOccurred'))
    }
  })

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: usersService.deleteUser,
    onSuccess: () => {
      toast.success(t('deletedSuccess'))
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowDeleteConfirm(false)
      setSelectedUser(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || t('errorOccurred'))
    }
  })

  // Toggle user status mutation
  const toggleStatusMutation = useMutation({
    mutationFn: usersService.toggleUserStatus,
    onSuccess: () => {
      toast.success(t('updatedSuccess'))
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || t('errorOccurred'))
    }
  })

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: ({ userId, password }: { userId: number; password: string }) =>
      usersService.resetUserPassword(userId, password),
    onSuccess: () => {
      toast.success(t('passwordChanged'))
      setShowResetPasswordModal(false)
      setSelectedUser(null)
      resetPasswordForm.reset()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        const messages = detail.map((err: any) => err.msg || err.message).join(', ')
        toast.error(messages || t('errorOccurred'))
      } else if (typeof detail === 'string') {
        toast.error(detail)
      } else {
        toast.error(t('errorOccurred'))
      }
    }
  })

  // Handlers
  const handleCreate = (data: CreateUserData) => {
    if (!data.role_id) {
      toast.error(t('required'))
      return
    }
    createUserMutation.mutate(data)
  }

  const handleEdit = (user: User) => {
    setSelectedUser(user)
    editForm.reset({
      first_name: user.first_name,
      last_name: user.last_name,
      phone: user.phone,
      email: user.email || '',
      role_id: user.role_id,
      is_active: user.is_active
    })
    setShowEditModal(true)
  }

  const handleUpdate = (data: UpdateUserData) => {
    if (selectedUser) {
      updateUserMutation.mutate({ id: selectedUser.id, data })
    }
  }

  const handleDelete = (user: User) => {
    if (user.id === currentUser?.id) {
      toast.error(t('accessDenied'))
      return
    }
    setSelectedUser(user)
    setShowDeleteConfirm(true)
  }

  const handleResetPassword = (user: User) => {
    setSelectedUser(user)
    resetPasswordForm.reset()
    setShowResetPasswordModal(true)
  }

  const submitResetPassword = (data: { new_password: string; confirm_password: string }) => {
    if (data.new_password !== data.confirm_password) {
      toast.error(t('passwordMismatch'))
      return
    }
    if (data.new_password.length < 6) {
      toast.error(t('minLength'))
      return
    }
    if (selectedUser) {
      resetPasswordMutation.mutate({ userId: selectedUser.id, password: data.new_password })
    }
  }

  const getRoleBadgeColor = (roleType: string) => {
    switch (roleType) {
      case 'admin': return 'bg-red-100 text-red-800'
      case 'manager': return 'bg-blue-100 text-blue-800'
      case 'cashier': return 'bg-green-100 text-green-800'
      case 'warehouse': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getRoleDisplayName = (roleName: string) => {
    const roleMap: Record<string, string> = {
      'Admin': t('director'),
      'ADMIN': t('director'),
      'admin': t('director'),
      'Manager': t('warehouseManager'),
      'MANAGER': t('warehouseManager'),
      'manager': t('warehouseManager'),
      'Cashier': t('seller2'),
      'CASHIER': t('seller2'),
      'cashier': t('seller2'),
      'Warehouse': t('warehouseManager'),
      'WAREHOUSE': t('warehouseManager'),
      'warehouse': t('warehouseManager'),
    }
    return roleMap[roleName] || roleName
  }

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 lg:gap-4">
        <div className="flex items-center gap-2 lg:gap-3">
          <UsersIcon className="w-6 h-6 lg:w-8 lg:h-8 text-primary" />
          <div>
            <h1 className="text-xl lg:text-2xl font-bold">{t('users')}</h1>
            <p className="text-xs lg:text-sm text-gray-500">{t('total')}: {users.length}</p>
          </div>
        </div>
        <Button variant="primary" onClick={() => setShowCreateModal(true)} className="w-full sm:w-auto">
          <Plus className="w-5 h-5 mr-2" />
          {t('addUser')}
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-3 lg:p-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 lg:gap-4">
            <div className="relative col-span-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 lg:w-5 lg:h-5 text-gray-400" />
              <Input
                placeholder={t('search') + '...'}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 lg:pl-10 text-sm lg:text-base"
              />
            </div>
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value ? Number(e.target.value) : '')}
              className="px-3 lg:px-4 py-2.5 lg:py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 text-sm lg:text-base"
            >
              <option value="">{t('all')} {t('role').toLowerCase()}</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>{getRoleDisplayName(role.name)}</option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 lg:px-4 py-2.5 lg:py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 text-sm lg:text-base"
            >
              <option value="">{t('all')} {t('status').toLowerCase()}</option>
              <option value="active">{t('active')}</option>
              <option value="inactive">{t('blocked')}</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <UsersIcon className="w-12 h-12 lg:w-16 lg:h-16 mx-auto mb-4 opacity-50" />
              <p className="text-sm lg:text-base">{t('noData')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[800px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-6 py-4 font-semibold">{t('name')}</th>
                    <th className="text-left px-6 py-4 font-semibold">{t('username')}</th>
                    <th className="text-left px-6 py-4 font-semibold">{t('phone')}</th>
                    <th className="text-left px-6 py-4 font-semibold">{t('role')}</th>
                    <th className="text-center px-6 py-4 font-semibold">{t('status')}</th>
                    <th className="text-left px-6 py-4 font-semibold">{t('date')}</th>
                    <th className="text-center px-6 py-4 font-semibold">{t('actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                            <span className="font-semibold text-primary">
                              {user.first_name[0]}{user.last_name[0]}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium">{user.first_name} {user.last_name}</p>
                            {user.email && (
                              <p className="text-sm text-gray-500">{user.email}</p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <code className="bg-gray-100 px-2 py-1 rounded text-sm">{user.username}</code>
                      </td>
                      <td className="px-6 py-4">{user.phone}</td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRoleBadgeColor(user.role_name?.toLowerCase() || '')}`}>
                          <Shield className="w-3 h-3 inline mr-1" />
                          {getRoleDisplayName(user.role_name || '')}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => toggleStatusMutation.mutate(user.id)}
                          disabled={user.id === currentUser?.id}
                          className={`p-2 rounded-lg transition-colors ${
                            user.is_active 
                              ? 'bg-green-100 text-green-600 hover:bg-green-200' 
                              : 'bg-red-100 text-red-600 hover:bg-red-200'
                          } ${user.id === currentUser?.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          {user.is_active ? <UserCheck className="w-5 h-5" /> : <UserX className="w-5 h-5" />}
                        </button>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {user.last_login 
                          ? formatDateTimeTashkent(user.last_login)
                          : '-'}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleEdit(user)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title={t('edit')}
                          >
                            <Edit className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleResetPassword(user)}
                            className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
                            title={t('changePassword')}
                          >
                            <Key className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(user)}
                            disabled={user.id === currentUser?.id}
                            className={`p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors ${
                              user.id === currentUser?.id ? 'opacity-50 cursor-not-allowed' : ''
                            }`}
                            title={t('delete')}
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
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

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-bold">{t('addUser')}</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={createForm.handleSubmit(handleCreate)} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">{t('firstName')} *</label>
                  <Input {...createForm.register('first_name', { required: true })} placeholder={t('firstName')} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t('lastName')} *</label>
                  <Input {...createForm.register('last_name', { required: true })} placeholder={t('lastName')} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('username')} *</label>
                <Input {...createForm.register('username', { required: true, minLength: 3 })} placeholder={t('username')} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('password')} *</label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    {...createForm.register('password', { required: true, minLength: 6 })}
                    placeholder={t('password')}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('phone')} *</label>
                <Input {...createForm.register('phone', { required: true })} placeholder="+998901234567" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('email')}</label>
                <Input {...createForm.register('email')} type="email" placeholder="email@example.com" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('role')} *</label>
                <select
                  {...createForm.register('role_id', { required: true, valueAsNumber: true })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20"
                >
                  <option value={0}>{t('role')}</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>{getRoleDisplayName(role.name)}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setShowCreateModal(false)}>
                  {t('cancel')}
                </Button>
                <Button type="submit" variant="primary" className="flex-1" disabled={createUserMutation.isPending}>
                  {createUserMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : t('save')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-bold">{t('editUser')}</h2>
              <button onClick={() => setShowEditModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={editForm.handleSubmit(handleUpdate)} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">{t('firstName')}</label>
                  <Input {...editForm.register('first_name')} placeholder={t('firstName')} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t('lastName')}</label>
                  <Input {...editForm.register('last_name')} placeholder={t('lastName')} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('phone')}</label>
                <Input {...editForm.register('phone')} placeholder="+998901234567" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('email')}</label>
                <Input {...editForm.register('email')} type="email" placeholder="email@example.com" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('role')}</label>
                <select
                  {...editForm.register('role_id', { valueAsNumber: true })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20"
                  disabled={selectedUser.id === currentUser?.id}
                >
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>{getRoleDisplayName(role.name)}</option>
                  ))}
                </select>
                {selectedUser.id === currentUser?.id && (
                  <p className="text-xs text-gray-500 mt-1">{t('accessDenied')}</p>
                )}
              </div>
              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setShowEditModal(false)}>
                  {t('cancel')}
                </Button>
                <Button type="submit" variant="primary" className="flex-1" disabled={updateUserMutation.isPending}>
                  {updateUserMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : t('save')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {showResetPasswordModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-bold">{t('changePassword')}</h2>
              <button onClick={() => setShowResetPasswordModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={resetPasswordForm.handleSubmit(submitResetPassword)} className="p-6 space-y-4">
              <div className="bg-yellow-50 p-4 rounded-xl">
                <p className="text-sm text-yellow-800">
                  <strong>{selectedUser.first_name} {selectedUser.last_name}</strong>
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('newPassword')}</label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    {...resetPasswordForm.register('new_password', { required: true, minLength: 6 })}
                    placeholder={t('newPassword')}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('confirmPassword')}</label>
                <Input
                  type={showPassword ? 'text' : 'password'}
                  {...resetPasswordForm.register('confirm_password', { required: true })}
                  placeholder={t('confirmPassword')}
                />
              </div>
              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setShowResetPasswordModal(false)}>
                  {t('cancel')}
                </Button>
                <Button type="submit" variant="warning" className="flex-1" disabled={resetPasswordMutation.isPending}>
                  {resetPasswordMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : t('save')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="text-xl font-bold mb-2">{t('confirm')}</h3>
              <p className="text-gray-600 mb-6">
                <strong>{selectedUser.first_name} {selectedUser.last_name}</strong> - {t('deleteUser')}?
              </p>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => setShowDeleteConfirm(false)}>
                  {t('cancel')}
                </Button>
                <Button
                  variant="danger"
                  className="flex-1"
                  onClick={() => deleteUserMutation.mutate(selectedUser.id)}
                  disabled={deleteUserMutation.isPending}
                >
                  {deleteUserMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : t('delete')}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
