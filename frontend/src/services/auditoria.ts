import api from './api'

export type TipoAccion =
  | 'crear'
  | 'actualizar'
  | 'eliminar'
  | 'login'
  | 'logout'
  | 'ver'
  | 'exportar'
  | 'asignar'
  | 'desasignar'
  | 'cambiar_estado'
  | 'subir_archivo'

export type ModuloAuditado =
  | 'auth'
  | 'usuarios'
  | 'proyectos'
  | 'etapas'
  | 'items_trabajo'
  | 'materiales'
  | 'equipos'
  | 'gastos'
  | 'clientes'
  | 'fotos'
  | 'reportes'
  | 'finanzas'
  | 'alertas'
  | 'jornadas'

export interface Auditoria {
  id: string
  usuario_id?: string
  usuario_nombre?: string
  accion: TipoAccion
  modulo: ModuloAuditado
  descripcion: string
  recurso_id?: string
  recurso_tipo?: string
  datos_adicionales?: Record<string, any>
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface ResumenActividad {
  periodo: {
    desde: string
    hasta: string
  }
  total_acciones: number
  acciones_por_tipo: Record<string, number>
  acciones_por_modulo: Record<string, number>
  usuarios_mas_activos: Array<{
    usuario_id: string
    usuario_nombre: string
    cantidad: number
  }>
}

export interface FiltrosAuditoria {
  usuario_id?: string
  modulo?: ModuloAuditado
  accion?: TipoAccion
  fecha_desde?: string
  fecha_hasta?: string
  recurso_id?: string
  skip?: number
  limit?: number
}

export const auditoriaService = {
  getAuditorias: async (filtros?: FiltrosAuditoria): Promise<Auditoria[]> => {
    const response = await api.get('/auditoria', { params: filtros })
    return response.data
  },

  getAuditoriaUsuario: async (usuarioId: string, limit: number = 50): Promise<Auditoria[]> => {
    const response = await api.get(`/auditoria/usuario/${usuarioId}`, { params: { limit } })
    return response.data
  },

  getAuditoriaRecurso: async (recursoId: string, limit: number = 50): Promise<Auditoria[]> => {
    const response = await api.get(`/auditoria/recurso/${recursoId}`, { params: { limit } })
    return response.data
  },

  getResumenActividad: async (
    fechaDesde?: string,
    fechaHasta?: string
  ): Promise<ResumenActividad> => {
    const response = await api.get('/auditoria/resumen', {
      params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta }
    })
    return response.data
  },

  getLoginsUsuario: async (usuarioId: string, limit: number = 20): Promise<Auditoria[]> => {
    const response = await api.get(`/auditoria/logins/${usuarioId}`, { params: { limit } })
    return response.data
  },

  getActividadReciente: async (limit: number = 20): Promise<Auditoria[]> => {
    const response = await api.get('/auditoria/reciente', { params: { limit } })
    return response.data
  },

  getTiposAccion: async (): Promise<{ value: string; label: string }[]> => {
    const response = await api.get('/auditoria/tipos')
    return response.data
  },

  getModulos: async (): Promise<{ value: string; label: string }[]> => {
    const response = await api.get('/auditoria/modulos')
    return response.data
  }
}

// Helpers
export const getAccionColor = (accion: TipoAccion): string => {
  const colors: Record<TipoAccion, string> = {
    crear: 'text-green-600 bg-green-100',
    actualizar: 'text-blue-600 bg-blue-100',
    eliminar: 'text-red-600 bg-red-100',
    login: 'text-purple-600 bg-purple-100',
    logout: 'text-gray-600 bg-gray-100',
    ver: 'text-cyan-600 bg-cyan-100',
    exportar: 'text-orange-600 bg-orange-100',
    asignar: 'text-indigo-600 bg-indigo-100',
    desasignar: 'text-pink-600 bg-pink-100',
    cambiar_estado: 'text-yellow-600 bg-yellow-100',
    subir_archivo: 'text-teal-600 bg-teal-100'
  }
  return colors[accion] || 'text-gray-600 bg-gray-100'
}

export const getAccionLabel = (accion: TipoAccion): string => {
  const labels: Record<TipoAccion, string> = {
    crear: 'Creacion',
    actualizar: 'Actualizacion',
    eliminar: 'Eliminacion',
    login: 'Inicio de Sesion',
    logout: 'Cierre de Sesion',
    ver: 'Visualizacion',
    exportar: 'Exportacion',
    asignar: 'Asignacion',
    desasignar: 'Desasignacion',
    cambiar_estado: 'Cambio de Estado',
    subir_archivo: 'Subida de Archivo'
  }
  return labels[accion] || accion
}

export const getModuloLabel = (modulo: ModuloAuditado): string => {
  const labels: Record<ModuloAuditado, string> = {
    auth: 'Autenticacion',
    usuarios: 'Usuarios',
    proyectos: 'Proyectos',
    etapas: 'Etapas',
    items_trabajo: 'Items de Trabajo',
    materiales: 'Materiales',
    equipos: 'Equipos',
    gastos: 'Gastos',
    clientes: 'Clientes',
    fotos: 'Fotos',
    reportes: 'Reportes',
    finanzas: 'Finanzas',
    alertas: 'Alertas',
    jornadas: 'Jornadas'
  }
  return labels[modulo] || modulo
}
