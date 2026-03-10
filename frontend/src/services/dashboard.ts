import api from './api'
import type { DashboardResumen, Alerta, Proyecto, Foto, ResumenFinancieroProyecto } from '@/types'

export const dashboardService = {
  async getResumen(): Promise<DashboardResumen> {
    const response = await api.get<DashboardResumen>('/dashboard/resumen')
    return response.data
  },

  async getAlertas(): Promise<Alerta[]> {
    const response = await api.get<Alerta[]>('/dashboard/alertas')
    return response.data
  },

  async getProyectosActivos(): Promise<Array<{
    id: string
    nombre: string
    estado: string
    porcentaje_avance: number
    fecha_fin_estimada?: string
    dias_restantes?: number
  }>> {
    const response = await api.get('/dashboard/proyectos-activos')
    return response.data
  },

  async getResumenFinanciero(): Promise<{
    ingresos_totales: number
    gastos_totales: number
    rentabilidad: number
    proyectos: ResumenFinancieroProyecto[]
  }> {
    const response = await api.get('/dashboard/financiero')
    return response.data
  },

  async getUltimasFotos(limit: number = 6): Promise<Array<{
    id: string
    url: string
    descripcion?: string
    fecha: string
    proyecto_id: string
    proyecto_nombre?: string
  }>> {
    const response = await api.get('/dashboard/ultimas-fotos', {
      params: { limit },
    })
    return response.data
  },

  async getActividadReciente(limit: number = 10): Promise<Array<{
    tipo: string
    mensaje: string
    fecha: string
    monto?: number
    usuario?: string
    proyecto?: string
  }>> {
    const response = await api.get('/dashboard/actividad-reciente', {
      params: { limit },
    })
    return response.data
  },
}
