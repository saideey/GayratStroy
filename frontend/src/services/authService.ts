import api from './api'
import type { LoginCredentials, AuthResponse, User } from '@/types'

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', credentials)
    return response.data
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout')
    } catch {
      // Ignore logout errors
    }
  },

  async getMe(): Promise<User> {
    const response = await api.get<{ success: boolean; data: User }>('/auth/me')
    return response.data.data
  },

  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data.tokens || response.data
  },
}
