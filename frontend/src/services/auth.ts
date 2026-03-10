import api from './api'
import type { AuthTokens, Usuario, LoginCredentials } from '@/types'

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await api.post<AuthTokens>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    const { access_token, refresh_token } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)

    return response.data
  },

  async getCurrentUser(): Promise<Usuario> {
    const response = await api.get<Usuario>('/auth/me')
    return response.data
  },

  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await api.post<{ access_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  async changePassword(passwordActual: string, passwordNuevo: string): Promise<void> {
    await api.post('/auth/cambiar-password', {
      password_actual: passwordActual,
      password_nuevo: passwordNuevo,
    })
  },

  logout(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  },
}
