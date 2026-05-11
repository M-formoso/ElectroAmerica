import api from './api'

export interface Deposito {
  id: string
  cliente_id: string
  cliente_nombre?: string
  nombre: string
  direccion?: string
  descripcion?: string
  activo: boolean
  created_at: string
  cantidad_materiales: number
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
}

export interface DepositoCreate {
  cliente_id: string
  nombre: string
  direccion?: string
  descripcion?: string
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

export const depositosService = {
  async list(clienteId?: string): Promise<Deposito[]> {
    const params = clienteId ? { cliente_id: clienteId } : undefined
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
}
