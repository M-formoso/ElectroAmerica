import api from './api'

export interface Usuario {
  id: string
  email: string
  nombre: string
  apellido: string
  telefono?: string
  rol: 'administrador' | 'supervisor' | 'operario' | 'cliente'
  activo: boolean
  created_at: string
  modulos_permitidos?: string[] | null
  es_superadmin: boolean
}

export interface UsuarioCreate {
  email: string
  password: string
  nombre: string
  apellido: string
  telefono?: string
  rol: string
  modulos_permitidos?: string[]
  es_superadmin?: boolean
}

export interface UsuarioUpdate {
  email?: string
  password?: string
  nombre?: string
  apellido?: string
  telefono?: string
  rol?: string
  activo?: boolean
  modulos_permitidos?: string[]
  es_superadmin?: boolean
}

export interface ModulosDisponibles {
  modulos: string[]
}

export interface ModulosPorRol {
  [rol: string]: string[]
}

export interface ModulosEfectivos {
  modulos: string[]
  es_superadmin: boolean
}

// Labels para mostrar los módulos en español
export const moduloLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  proyectos: 'Proyectos',
  clientes: 'Clientes',
  materiales: 'Materiales',
  depositos: 'Depósitos',
  remitos: 'Remitos',
  equipos: 'Equipos',
  herramientas: 'Herramientas',
  finanzas: 'Finanzas',
  reportes: 'Reportes',
  usuarios: 'Usuarios',
  alertas: 'Alertas',
  auditoria: 'Auditoría',
  jornadas_operario: 'Mi Jornada (Operario)',
  jornadas_gestion: 'Gestión de Jornadas',
  actividades_tipo: 'Actividades Tipo',
}

export const usuariosService = {
  async getUsuarios(params?: {
    rol?: string
    skip?: number
    limit?: number
  }): Promise<Usuario[]> {
    const response = await api.get<Usuario[]>('/usuarios/', { params })
    return response.data
  },

  async getUsuario(id: string): Promise<Usuario> {
    const response = await api.get<Usuario>(`/usuarios/${id}`)
    return response.data
  },

  async createUsuario(data: UsuarioCreate): Promise<Usuario> {
    const response = await api.post<Usuario>('/usuarios/', data)
    return response.data
  },

  async updateUsuario(id: string, data: UsuarioUpdate): Promise<Usuario> {
    const response = await api.put<Usuario>(`/usuarios/${id}`, data)
    return response.data
  },

  async deleteUsuario(id: string): Promise<void> {
    await api.delete(`/usuarios/${id}`)
  },

  async getClientes(): Promise<Usuario[]> {
    const response = await api.get<Usuario[]>('/usuarios/clientes')
    return response.data
  },

  // Nuevos endpoints para módulos
  async getModulosDisponibles(): Promise<ModulosDisponibles> {
    const response = await api.get<ModulosDisponibles>('/usuarios/config/modulos-disponibles')
    return response.data
  },

  async getModulosPorRol(): Promise<ModulosPorRol> {
    const response = await api.get<ModulosPorRol>('/usuarios/config/modulos-por-rol')
    return response.data
  },

  async updateModulosUsuario(id: string, modulos: string[]): Promise<Usuario> {
    const response = await api.put<Usuario>(`/usuarios/${id}/modulos`, modulos)
    return response.data
  },

  async getModulosEfectivos(id: string): Promise<ModulosEfectivos> {
    const response = await api.get<ModulosEfectivos>(`/usuarios/${id}/modulos-efectivos`)
    return response.data
  },
}
