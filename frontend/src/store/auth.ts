import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Usuario } from '@/types'
import { authService } from '@/services/auth'

// Módulos por defecto según rol (mismo que backend)
const MODULOS_POR_ROL: Record<string, string[]> = {
  administrador: [
    'dashboard', 'proyectos', 'clientes', 'materiales', 'depositos', 'remitos', 'equipos',
    'herramientas', 'finanzas', 'reportes', 'usuarios', 'alertas',
    'auditoria', 'jornadas_operario', 'jornadas_gestion', 'actividades_tipo'
  ],
  supervisor: [
    'dashboard', 'proyectos', 'clientes', 'materiales', 'depositos', 'remitos', 'equipos',
    'herramientas', 'finanzas', 'reportes', 'alertas',
    'jornadas_gestion', 'actividades_tipo'
  ],
  operario: [
    'dashboard', 'proyectos', 'materiales', 'equipos',
    'jornadas_operario'
  ],
  cliente: []
}

interface AuthState {
  user: Usuario | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  modulosEfectivos: string[]

  login: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  clearError: () => void
  tieneAccesoModulo: (modulo: string) => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: authService.isAuthenticated(),
      isLoading: false,
      error: null,
      modulosEfectivos: [],

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          await authService.login({ username: email, password })
          const user = await authService.getCurrentUser()
          const modulos = calcularModulosEfectivos(user)
          set({ user, isAuthenticated: true, isLoading: false, modulosEfectivos: modulos })
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Error al iniciar sesión'
          set({ error: message, isLoading: false })
          throw error
        }
      },

      logout: () => {
        authService.logout()
        set({ user: null, isAuthenticated: false, modulosEfectivos: [] })
      },

      fetchUser: async () => {
        if (!authService.isAuthenticated()) {
          set({ user: null, isAuthenticated: false, modulosEfectivos: [] })
          return
        }

        set({ isLoading: true })
        try {
          const user = await authService.getCurrentUser()
          const modulos = calcularModulosEfectivos(user)
          set({ user, isAuthenticated: true, isLoading: false, modulosEfectivos: modulos })
        } catch (error) {
          authService.logout()
          set({ user: null, isAuthenticated: false, isLoading: false, modulosEfectivos: [] })
        }
      },

      clearError: () => set({ error: null }),

      tieneAccesoModulo: (modulo: string) => {
        const { modulosEfectivos } = get()
        return modulosEfectivos.includes(modulo)
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// Función helper para calcular módulos efectivos
function calcularModulosEfectivos(user: Usuario | null): string[] {
  if (!user) return []

  // Si es superadmin, tiene todos los módulos
  if (user.es_superadmin) {
    return MODULOS_POR_ROL.administrador
  }

  // Si tiene módulos personalizados, usar esos
  if (user.modulos_permitidos && user.modulos_permitidos.length > 0) {
    return user.modulos_permitidos
  }

  // Sino, usar los del rol
  return MODULOS_POR_ROL[user.rol] || []
}

// Selector helpers
export const useUser = () => useAuthStore((state) => state.user)
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated)
export const useIsAdmin = () => useAuthStore((state) => state.user?.rol === 'administrador')
export const useIsSupervisor = () => useAuthStore((state) => state.user?.rol === 'supervisor')
export const useIsOperario = () => useAuthStore((state) => state.user?.rol === 'operario')
export const useIsCliente = () => useAuthStore((state) => state.user?.rol === 'cliente')
export const useIsSuperadmin = () => useAuthStore((state) => state.user?.es_superadmin === true)
export const useIsStaff = () =>
  useAuthStore((state) =>
    ['administrador', 'supervisor', 'operario'].includes(state.user?.rol || '')
  )
export const useModulosEfectivos = () => useAuthStore((state) => state.modulosEfectivos)
export const useTieneAccesoModulo = (modulo: string) =>
  useAuthStore((state) => state.modulosEfectivos.includes(modulo))
