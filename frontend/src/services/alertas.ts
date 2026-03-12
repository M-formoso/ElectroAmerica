import api from './api'

export type TipoAlerta =
  | 'stock_minimo'
  | 'demora_etapa'
  | 'etapa_pendiente'
  | 'limite_credito'
  | 'equipo_mantenimiento'
  | 'proyecto_vencido'
  | 'pago_pendiente'

export type PrioridadAlerta = 'baja' | 'media' | 'alta' | 'critica'

export interface Alerta {
  id: string
  tipo: TipoAlerta
  prioridad: PrioridadAlerta
  titulo: string
  mensaje: string
  referencia_tipo?: string
  referencia_id?: string
  usuario_id?: string
  leida: boolean
  resuelta: boolean
  fecha_resolucion?: string
  resuelto_por_id?: string
  created_at: string
}

export interface AlertaConteo {
  total: number
  criticas: number
  altas: number
  medias: number
  bajas: number
  no_leidas: number
}

export interface VerificacionResultado {
  stock_minimo: number
  demoras_etapas: number
  equipos_mantenimiento: number
  limites_credito: number
  proyectos_vencidos: number
  total: number
}

export const alertasService = {
  getAlertas: async (params?: {
    solo_no_leidas?: boolean
    solo_no_resueltas?: boolean
    tipo?: TipoAlerta
    prioridad?: PrioridadAlerta
    skip?: number
    limit?: number
  }): Promise<Alerta[]> => {
    const response = await api.get('/alertas', { params })
    return response.data
  },

  getConteo: async (): Promise<AlertaConteo> => {
    const response = await api.get('/alertas/conteo')
    return response.data
  },

  marcarLeida: async (alertaId: string): Promise<Alerta> => {
    const response = await api.post(`/alertas/${alertaId}/leer`)
    return response.data
  },

  marcarTodasLeidas: async (): Promise<{ message: string }> => {
    const response = await api.post('/alertas/leer-todas')
    return response.data
  },

  resolverAlerta: async (alertaId: string): Promise<Alerta> => {
    const response = await api.post(`/alertas/${alertaId}/resolver`)
    return response.data
  },

  ejecutarVerificaciones: async (): Promise<VerificacionResultado> => {
    const response = await api.post('/alertas/verificar')
    return response.data
  },

  getTipos: async (): Promise<{ value: string; label: string }[]> => {
    const response = await api.get('/alertas/tipos')
    return response.data
  },

  getPrioridades: async (): Promise<{ value: string; label: string }[]> => {
    const response = await api.get('/alertas/prioridades')
    return response.data
  }
}

// Helpers
export const getPrioridadColor = (prioridad: PrioridadAlerta): string => {
  const colors = {
    baja: 'text-gray-500 bg-gray-100',
    media: 'text-blue-500 bg-blue-100',
    alta: 'text-orange-500 bg-orange-100',
    critica: 'text-red-500 bg-red-100'
  }
  return colors[prioridad] || colors.media
}

export const getTipoIcon = (tipo: TipoAlerta): string => {
  const icons = {
    stock_minimo: 'Package',
    demora_etapa: 'Clock',
    etapa_pendiente: 'AlertTriangle',
    limite_credito: 'CreditCard',
    equipo_mantenimiento: 'Wrench',
    proyecto_vencido: 'Calendar',
    pago_pendiente: 'DollarSign'
  }
  return icons[tipo] || 'Bell'
}

export const getTipoLabel = (tipo: TipoAlerta): string => {
  const labels = {
    stock_minimo: 'Stock Mínimo',
    demora_etapa: 'Demora en Etapa',
    etapa_pendiente: 'Etapa Pendiente',
    limite_credito: 'Límite de Crédito',
    equipo_mantenimiento: 'Mantenimiento Equipo',
    proyecto_vencido: 'Proyecto Vencido',
    pago_pendiente: 'Pago Pendiente'
  }
  return labels[tipo] || tipo
}
