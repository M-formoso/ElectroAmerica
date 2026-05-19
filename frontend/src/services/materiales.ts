import api from './api'
import type { Material } from '@/types'

export interface DestinoInicialStock {
  deposito_id: string
  cantidad: number
}

export interface MaterialCreatePayload extends Partial<Material> {
  destinos_iniciales?: DestinoInicialStock[]
}

export const materialesService = {
  async getMateriales(params?: {
    skip?: number
    limit?: number
    busqueda?: string
  }): Promise<Material[]> {
    const response = await api.get<Material[]>('/materiales/', {
      params: { limit: 1000, ...params },
    })
    return response.data
  },

  async getMaterial(id: string): Promise<Material> {
    const response = await api.get<Material>(`/materiales/${id}`)
    return response.data
  },

  async createMaterial(data: MaterialCreatePayload): Promise<Material> {
    const response = await api.post<Material>('/materiales/', data)
    return response.data
  },

  async transferirADeposito(
    materialId: string,
    payload: { deposito_id: string; cantidad: number; motivo?: string }
  ): Promise<MovimientoStock> {
    const response = await api.post<MovimientoStock>(
      `/materiales/${materialId}/transferir-a-deposito`,
      payload
    )
    return response.data
  },

  async updateMaterial(id: string, data: Partial<Material>): Promise<Material> {
    const response = await api.put<Material>(`/materiales/${id}`, data)
    return response.data
  },

  async deleteMaterial(id: string): Promise<void> {
    await api.delete(`/materiales/${id}`)
  },

  async registrarEntrada(
    materialId: string,
    cantidad: number,
    motivo?: string
  ): Promise<any> {
    const response = await api.post('/materiales/ingreso', {
      material_id: materialId,
      cantidad,
      motivo,
    })
    return response.data
  },

  async registrarSalida(
    materialId: string,
    cantidad: number,
    motivo?: string,
    proyectoId?: string
  ): Promise<any> {
    // Usamos asignar para registrar salida (requiere proyecto)
    const response = await api.post('/materiales/asignar', {
      material_id: materialId,
      proyecto_id: proyectoId,
      cantidad,
      observaciones: motivo,
    })
    return response.data
  },

  async getStockBajo(): Promise<Material[]> {
    const response = await api.get<Material[]>('/materiales/stock-bajo')
    return response.data
  },

  async asignarMaterial(data: {
    material_id: string
    proyecto_id: string
    etapa_id?: string
    cantidad: number
    notas?: string
  }): Promise<any> {
    const response = await api.post('/materiales/asignar', {
      ...data,
      fecha_asignacion: new Date().toISOString().split('T')[0],
    })
    return response.data
  },

  async getAsignacionesProyecto(proyectoId: string): Promise<any[]> {
    const response = await api.get(`/proyectos/${proyectoId}/materiales`)
    return response.data
  },

  async getMovimientos(materialId: string, limit: number = 50): Promise<MovimientoStock[]> {
    const response = await api.get(`/materiales/${materialId}/movimientos`, { params: { limit } })
    return response.data
  },

  async getValorInventario(): Promise<ValorInventario> {
    const response = await api.get('/materiales/valor-total')
    return response.data
  },

  async getUbicaciones(): Promise<string[]> {
    const response = await api.get('/materiales/ubicaciones')
    return response.data.ubicaciones
  },
}

export interface MovimientoStock {
  id: string
  material_id: string
  tipo: 'entrada' | 'salida' | 'ajuste' | 'devolucion' | 'transferencia_a_deposito'
  cantidad: number
  stock_anterior: number
  stock_nuevo: number
  motivo?: string
  proyecto_id?: string
  proyecto_nombre?: string
  deposito_id?: string
  deposito_nombre?: string
  deposito_destino_id?: string
  deposito_destino_nombre?: string
  usuario_id: string
  usuario_nombre?: string
  created_at: string
}

export interface ValorInventario {
  valor_total: number
  total_items: number
  items_stock_bajo: number
}
