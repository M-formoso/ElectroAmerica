import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Usuario } from '@/types'
import { authService } from '@/services/auth'

interface AuthState {
  user: Usuario | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: authService.isAuthenticated(),
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          await authService.login({ username: email, password })
          const user = await authService.getCurrentUser()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Error al iniciar sesión'
          set({ error: message, isLoading: false })
          throw error
        }
      },

      logout: () => {
        authService.logout()
        set({ user: null, isAuthenticated: false })
      },

      fetchUser: async () => {
        if (!authService.isAuthenticated()) {
          set({ user: null, isAuthenticated: false })
          return
        }

        set({ isLoading: true })
        try {
          const user = await authService.getCurrentUser()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (error) {
          authService.logout()
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// Selector helpers
export const useUser = () => useAuthStore((state) => state.user)
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated)
export const useIsAdmin = () => useAuthStore((state) => state.user?.rol === 'administrador')
export const useIsSupervisor = () => useAuthStore((state) => state.user?.rol === 'supervisor')
export const useIsOperario = () => useAuthStore((state) => state.user?.rol === 'operario')
export const useIsCliente = () => useAuthStore((state) => state.user?.rol === 'cliente')
export const useIsStaff = () =>
  useAuthStore((state) =>
    ['administrador', 'supervisor', 'operario'].includes(state.user?.rol || '')
  )
