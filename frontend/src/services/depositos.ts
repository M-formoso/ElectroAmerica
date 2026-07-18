import api from './api'
import type { MovimientoStock } from './materiales'

export interface Deposito {
  id: string
  cliente_id: string
  cliente_nombre?: string
  parent_id?: string | null
  nombre: string
  direccion?: string
  descripcion?: string
  activo: boolean
  created_at: string
  cantidad_materiales: number
  cantidad_subdepositos: number
}

export interface MaterialAgregado {
  material_id: string
  material_codigo?: string
  material_nombre?: string
  material_unidad?: string
  stock_total: number
}

export interface DepositoMaterial {
  id: string
  deposito_id: string
  material_id: string
  stock_actual: number
  stock_minimo: number
  activo: boolean
  material_codigo?: string
  material_nombre?: string
  material_unidad?: string
}

export interface DepositoDetail extends Deposito {
  materiales: DepositoMaterial[]
  subdepositos: Deposito[]
  materiales_totales: MaterialAgregado[]
}

export interface DepositoCreate {
  cliente_id: string
  nombre: string
  direccion?: string
  descripcion?: string
  parent_id?: string
}

export interface DepositoUpdate {
  nombre?: string
  direccion?: string
  descripcion?: string
}

export interface DepositoMaterialCreate {
  material_id: string
  stock_actual?: number
  stock_minimo?: number
}

export interface DepositoMaterialUpdate {
  stock_actual?: number
  stock_minimo?: number
}

export interface DepositoMaterialBulkItem {
  material_id: string
  stock_actual: number
  stock_minimo: number
}

export interface DepositoMaterialNuevoPayload {
  codigo?: string
  nombre: string
  descripcion?: string
  unidad: string
  precio_unitario?: number
  stock_actual: number
  stock_minimo: number
}

export interface DepositoMovimientoPayload {
  cantidad: number
  motivo?: string
}

export const depositosService = {
  async list(clienteId?: string, parentId?: string): Promise<Deposito[]> {
    const params: Record<string, string | boolean> = {}
    if (clienteId) params.cliente_id = clienteId
    if (parentId) {
      params.parent_id = parentId
      params.only_roots = false
    }
    const response = await api.get<Deposito[]>('/depositos', { params })
    return response.data
  },

  async get(id: string): Promise<DepositoDetail> {
    const response = await api.get<DepositoDetail>(`/depositos/${id}`)
    return response.data
  },

  async create(data: DepositoCreate): Promise<Deposito> {
    const response = await api.post<Deposito>('/depositos', data)
    return response.data
  },

  async update(id: string, data: DepositoUpdate): Promise<Deposito> {
    const response = await api.put<Deposito>(`/depositos/${id}`, data)
    return response.data
  },

  async remove(id: string): Promise<void> {
    await api.delete(`/depositos/${id}`)
  },

  async descargarPdfStock(id: string, nombre: string): Promise<void> {
    const res = await api.get(`/depositos/${id}/stock/pdf`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    const safe = (nombre || 'deposito').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 40)
    link.download = `stock_${safe}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  async descargarPdfDetalleMovimientos(
    id: string,
    nombre: string,
    fechaDesde?: string,
    fechaHasta?: string,
  ): Promise<void> {
    const params: Record<string, string> = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta
    const res = await api.get(`/depositos/${id}/detalle-movimientos/pdf`, {
      params,
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    const safe = (nombre || 'deposito').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 40)
    link.download = `detalle_movimientos_${safe}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  async listMateriales(depositoId: string): Promise<DepositoMaterial[]> {
    const response = await api.get<DepositoMaterial[]>(
      `/depositos/${depositoId}/materiales`
    )
    return response.data
  },

  async addMaterial(
    depositoId: string,
    data: DepositoMaterialCreate
  ): Promise<DepositoMaterial> {
    const response = await api.post<DepositoMaterial>(
      `/depositos/${depositoId}/materiales`,
      data
    )
    return response.data
  },

  async updateMaterial(
    depositoId: string,
    materialId: string,
    data: DepositoMaterialUpdate
  ): Promise<DepositoMaterial> {
    const response = await api.put<DepositoMaterial>(
      `/depositos/${depositoId}/materiales/${materialId}`,
      data
    )
    return response.data
  },

  async removeMaterial(depositoId: string, materialId: string): Promise<void> {
    await api.delete(`/depositos/${depositoId}/materiales/${materialId}`)
  },

  async addMaterialesBulk(
    depositoId: string,
    items: DepositoMaterialBulkItem[]
  ): Promise<DepositoMaterial[]> {
    const response = await api.post<DepositoMaterial[]>(
      `/depositos/${depositoId}/materiales/bulk`,
      { items }
    )
    return response.data
  },

  async addMaterialNuevo(
    depositoId: string,
    data: DepositoMaterialNuevoPayload
  ): Promise<DepositoMaterial> {
    const response = await api.post<DepositoMaterial>(
      `/depositos/${depositoId}/materiales/nuevo`,
      data
    )
    return response.data
  },

  async entrada(
    depositoId: string,
    materialId: string,
    data: DepositoMovimientoPayload
  ): Promise<MovimientoStock> {
    const response = await api.post<MovimientoStock>(
      `/depositos/${depositoId}/materiales/${materialId}/entrada`,
      data
    )
    return response.data
  },

  async salida(
    depositoId: string,
    materialId: string,
    data: DepositoMovimientoPayload
  ): Promise<MovimientoStock> {
    const response = await api.post<MovimientoStock>(
      `/depositos/${depositoId}/materiales/${materialId}/salida`,
      data
    )
    return response.data
  },

  async getMovimientosMaterial(
    depositoId: string,
    materialId: string,
    limit = 50
  ): Promise<MovimientoStock[]> {
    const response = await api.get<MovimientoStock[]>(
      `/depositos/${depositoId}/materiales/${materialId}/movimientos`,
      { params: { limit } }
    )
    return response.data
  },
}
