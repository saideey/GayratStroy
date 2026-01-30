import api from './api'

export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  phone: string
  email?: string
  role_id: number
  role_name: string
  is_active: boolean
  created_at: string
  last_login?: string
}

export interface Role {
  id: number
  name: string
  role_type: string
  description?: string
  permissions: string[]
}

export interface CreateUserData {
  username: string
  password: string
  first_name: string
  last_name: string
  phone: string
  email?: string
  role_id: number
}

export interface UpdateUserData {
  first_name?: string
  last_name?: string
  phone?: string
  email?: string
  role_id?: number
  is_active?: boolean
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
}

export const usersService = {
  // Get all users
  getUsers: async (params?: { search?: string; role_id?: number; is_active?: boolean }) => {
    const response = await api.get('/users', { params })
    return response.data
  },

  // Get single user
  getUser: async (id: number) => {
    const response = await api.get(`/users/${id}`)
    return response.data
  },

  // Create user
  createUser: async (data: CreateUserData) => {
    const response = await api.post('/users', data)
    return response.data
  },

  // Update user
  updateUser: async (id: number, data: UpdateUserData) => {
    const response = await api.put(`/users/${id}`, data)
    return response.data
  },

  // Delete user
  deleteUser: async (id: number) => {
    const response = await api.delete(`/users/${id}`)
    return response.data
  },

  // Change password (own)
  changePassword: async (data: ChangePasswordData) => {
    const response = await api.post('/users/change-password', data)
    return response.data
  },

  // Reset user password (admin)
  resetUserPassword: async (userId: number, newPassword: string) => {
    const response = await api.post(`/users/${userId}/reset-password`, { new_password: newPassword })
    return response.data
  },

  // Get all roles
  getRoles: async () => {
    const response = await api.get('/users/roles')
    return response.data
  },

  // Toggle user status
  toggleUserStatus: async (id: number) => {
    const response = await api.patch(`/users/${id}/toggle-status`)
    return response.data
  }
}

export default usersService
