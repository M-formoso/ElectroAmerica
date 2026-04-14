import api from './api'

// ============ Enums ============

export type EstadoRequerimiento =
  | 'estimado'
  | 'aprobado'
  | 'pendiente_compra'
  | 'en_proceso_compra'
  | 'pendiente_entrega'
  | 'pendiente_retiro'
  | 'entregado_obra'
  | 'consumido'
  | 'cancelado'

export type OrigenMaterial = 'stock_propio' | 'compra' | 'entrega_cliente'

export type PrioridadRequerimiento = 'critica' | 'alta' | 'media' | 'baja'

// ============ Types ============

export interface EmpresaProveedora {
  id: string
  nombre: string
  tipo: string
  cuit?: string
  telefono?: string
  email?: string
  direccion?: string
  contacto_nombre?: string
  notas?: string
  activo: boolean
  created_at: string
}

export interface RequerimientoMaterial {
  id: string
  proyecto_id: string
  etapa_id?: string
  material_id: string

  cantidad_estimada: number
  cantidad_aprobada?: number
  cantidad_entregada: number
  cantidad_consumida: number
  cantidad_pendiente: number
  cantidad_disponible: number

  estado: EstadoRequerimiento
  prioridad: PrioridadRequerimiento
  origen?: OrigenMaterial
  empresa_origen_id?: string

  actividad_tipo_id?: string
  cantidad_trabajo?: number

  fecha_necesidad?: string
  fecha_solicitud?: string
  fecha_entrega?: string

  notas?: string
  notas_aprobacion?: string

  creado_por_id?: string
  aprobado_por_id?: string
  fecha_aprobacion?: string

  activo: boolean
  created_at: string
  updated_at: string

  // Datos relacionados
  material_nombre?: string
  material_unidad?: string
  material_stock?: number
  proyecto_nombre?: string
  etapa_nombre?: string
  actividad_tipo_nombre?: string
  empresa_origen_nombre?: string
}

export interface HistorialRequerimiento {
  id: string
  campo_modificado: string
  valor_anterior?: string
  valor_nuevo?: string
  motivo?: string
  usuario_nombre?: string
  created_at: string
}

export interface MaterialCalculado {
  material_id: string
  material_nombre: string
  material_unidad: string
  cantidad_total: number
  stock_disponible: number
  falta_stock: boolean
  actividades_origen: Array<{
    actividad_tipo_id: string
    actividad_nombre: string
    cantidad_trabajo: number
    cantidad_material: number
  }>
}

export interface ResumenMaterialesProyecto {
  proyecto_id: string
  proyecto_nombre: string
  total_requerimientos: number
  por_estado: Record<string, number>
  por_prioridad: Record<string, number>
  materiales_pendientes: number
  materiales_en_obra: number
  valor_estimado_total?: number
}

// ============ Request Types ============

export interface RequerimientoCreate {
  proyecto_id: string
  etapa_id?: string
  material_id: string
  cantidad_estimada: number
  prioridad?: PrioridadRequerimiento
  fecha_necesidad?: string
  notas?: string
  origen?: OrigenMaterial
  empresa_origen_id?: string
}

export interface RequerimientoFromActividad {
  proyecto_id: string
  etapa_id?: string
  actividad_tipo_id: string
  cantidad_trabajo: number
  fecha_necesidad?: string
  prioridad?: PrioridadRequerimiento
}

export interface RequerimientoUpdate {
  cantidad_estimada?: number
  cantidad_aprobada?: number
  prioridad?: PrioridadRequerimiento
  origen?: OrigenMaterial
  empresa_origen_id?: string
  fecha_necesidad?: string
  notas?: string
}

export interface CalculoMaterialesRequest {
  proyecto_id: string
  etapa_id?: string
  actividades: Array<{
    actividad_tipo_id: string
    cantidad_trabajo: number
  }>
  fecha_necesidad?: string
  prioridad?: PrioridadRequerimiento
  crear_requerimientos?: boolean
}

export interface CalculoMaterialesResponse {
  materiales: MaterialCalculado[]
  total_items: number
  items_sin_stock: number
  requerimientos_creados?: string[]
}

// ============ Labels y colores ============

export const estadoLabels: Record<EstadoRequerimiento, string> = {
  estimado: 'Estimado',
  aprobado: 'Aprobado',
  pendiente_compra: 'Pendiente Compra',
  en_proceso_compra: 'En Proceso Compra',
  pendiente_entrega: 'Pendiente Entrega',
  pendiente_retiro: 'Pendiente Retiro',
  entregado_obra: 'Entregado en Obra',
  consumido: 'Consumido',
  cancelado: 'Cancelado',
}

export const estadoColors: Record<EstadoRequerimiento, string> = {
  estimado: 'bg-gray-500',
  aprobado: 'bg-blue-500',
  pendiente_compra: 'bg-orange-500',
  en_proceso_compra: 'bg-yellow-500',
  pendiente_entrega: 'bg-purple-500',
  pendiente_retiro: 'bg-cyan-500',
  entregado_obra: 'bg-green-500',
  consumido: 'bg-green-700',
  cancelado: 'bg-red-500',
}

export const prioridadLabels: Record<PrioridadRequerimiento, string> = {
  critica: 'Crítica',
  alta: 'Alta',
  media: 'Media',
  baja: 'Baja',
}

export const prioridadColors: Record<PrioridadRequerimiento, string> = {
  critica: 'bg-red-600',
  alta: 'bg-orange-500',
  media: 'bg-blue-500',
  baja: 'bg-gray-400',
}

export const origenLabels: Record<OrigenMaterial, string> = {
  stock_propio: 'Stock Propio',
  compra: 'Compra',
  entrega_cliente: 'Entrega Cliente',
}

// ============ Service ============

export const requerimientosMaterialService = {
  // ============ Empresas Proveedoras ============

  async getEmpresas(tipo?: string): Promise<EmpresaProveedora[]> {
    const response = await api.get<EmpresaProveedora[]>('/requerimientos-material/empresas', {
      params: { tipo },
    })
    return response.data
  },

  async createEmpresa(data: Partial<EmpresaProveedora>): Promise<EmpresaProveedora> {
    const response = await api.post<EmpresaProveedora>('/requerimientos-material/empresas', data)
    return response.data
  },

  async updateEmpresa(id: string, data: Partial<EmpresaProveedora>): Promise<EmpresaProveedora> {
    const response = await api.put<EmpresaProveedora>(`/requerimientos-material/empresas/${id}`, data)
    return response.data
  },

  // ============ Requerimientos CRUD ============

  async getRequerimientos(params?: {
    proyecto_id?: string
    etapa_id?: string
    estado?: EstadoRequerimiento
    prioridad?: PrioridadRequerimiento
    origen?: OrigenMaterial
    pendientes?: boolean
    skip?: number
    limit?: number
  }): Promise<RequerimientoMaterial[]> {
    const response = await api.get<RequerimientoMaterial[]>('/requerimientos-material/', { params })
    return response.data
  },

  async getRequerimiento(id: string): Promise<RequerimientoMaterial> {
    const response = await api.get<RequerimientoMaterial>(`/requerimientos-material/${id}`)
    return response.data
  },

  async createRequerimiento(data: RequerimientoCreate): Promise<RequerimientoMaterial> {
    const response = await api.post<RequerimientoMaterial>('/requerimientos-material/', data)
    return response.data
  },

  async createDesdeActividad(data: RequerimientoFromActividad): Promise<RequerimientoMaterial[]> {
    const response = await api.post<RequerimientoMaterial[]>('/requerimientos-material/desde-actividad', data)
    return response.data
  },

  async updateRequerimiento(id: string, data: RequerimientoUpdate): Promise<RequerimientoMaterial> {
    const response = await api.put<RequerimientoMaterial>(`/requerimientos-material/${id}`, data)
    return response.data
  },

  async deleteRequerimiento(id: string): Promise<void> {
    await api.delete(`/requerimientos-material/${id}`)
  },

  // ============ Acciones ============

  async aprobar(
    id: string,
    data: { cantidad_aprobada: number; notas_aprobacion?: string }
  ): Promise<RequerimientoMaterial> {
    const response = await api.post<RequerimientoMaterial>(`/requerimientos-material/${id}/aprobar`, data)
    return response.data
  },

  async cambiarEstado(
    id: string,
    data: { estado: EstadoRequerimiento; motivo?: string; origen?: OrigenMaterial; empresa_origen_id?: string }
  ): Promise<RequerimientoMaterial> {
    const response = await api.post<RequerimientoMaterial>(`/requerimientos-material/${id}/cambiar-estado`, data)
    return response.data
  },

  async registrarEntrega(
    id: string,
    data: { cantidad_entregada: number; notas?: string }
  ): Promise<RequerimientoMaterial> {
    const response = await api.post<RequerimientoMaterial>(`/requerimientos-material/${id}/registrar-entrega`, data)
    return response.data
  },

  async registrarConsumo(
    id: string,
    data: { cantidad_consumida: number; notas?: string }
  ): Promise<RequerimientoMaterial> {
    const response = await api.post<RequerimientoMaterial>(`/requerimientos-material/${id}/registrar-consumo`, data)
    return response.data
  },

  // ============ Historial ============

  async getHistorial(requerimientoId: string): Promise<HistorialRequerimiento[]> {
    const response = await api.get<HistorialRequerimiento[]>(
      `/requerimientos-material/${requerimientoId}/historial`
    )
    return response.data
  },

  // ============ Cálculo ============

  async calcularMateriales(data: CalculoMaterialesRequest): Promise<CalculoMaterialesResponse> {
    const response = await api.post<CalculoMaterialesResponse>('/requerimientos-material/calcular', data)
    return response.data
  },

  async getResumenProyecto(proyectoId: string): Promise<ResumenMaterialesProyecto> {
    const response = await api.get<ResumenMaterialesProyecto>(
      `/requerimientos-material/proyecto/${proyectoId}/resumen`
    )
    return response.data
  },
}
