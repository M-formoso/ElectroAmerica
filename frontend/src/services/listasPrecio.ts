import api from './api'

export interface ListaPrecio {
  id: string
  nombre: string
  descripcion?: string | null
  activo: boolean
  created_at: string
  cantidad_actividades_con_precio: number
}

export interface PrecioActividadItem {
  actividad_tipo_id: string
  actividad_codigo?: string | null
  actividad_nombre: string
  actividad_unidad?: string | null
  precio_unitario: number
}

export interface ListaPrecioDetail extends ListaPrecio {
  items: PrecioActividadItem[]
}

export interface PrecioBulkItem {
  actividad_tipo_id: string
  precio_unitario: number
}

export interface TotalProyectoItem {
  proyecto_id: string
  proyecto_nombre: string
  cliente_nombre?: string | null
  estado?: string | null
  lista_precio_id?: string | null
  lista_precio_nombre?: string | null
  cantidad_actividades: number
  total_presupuestado: number
  total_ejecutado: number
}

export interface DetalleActividadPresupuesto {
  proyecto_actividad_id: string
  actividad_tipo_id: string
  actividad_codigo?: string | null
  actividad_nombre: string
  unidad?: string | null
  cantidad_planificada: number
  cantidad_ejecutada: number
  precio_unitario_snapshot: number
  subtotal_presupuestado: number
  subtotal_ejecutado: number
}

export interface DetallePresupuestoProyecto {
  proyecto_id: string
  proyecto_nombre: string
  cliente_nombre?: string | null
  lista_precio_nombre?: string | null
  total_presupuestado: number
  total_ejecutado: number
  items: DetalleActividadPresupuesto[]
}

export type EstadoFacturacion = 'pendiente' | 'facturado' | 'cobrado'

export interface FacturacionProyectoItem {
  proyecto_id: string
  proyecto_nombre: string
  cliente_nombre?: string | null
  fecha_fin_real?: string | null
  estado_facturacion: EstadoFacturacion
  numero_factura?: string | null
  fecha_facturacion?: string | null
  fecha_cobro?: string | null
  monto_facturado?: number | null
  total_presupuestado: number
  total_ejecutado: number
}

export interface FacturarProyectoBody {
  numero_factura: string
  fecha_facturacion: string
  monto_facturado?: number | null
}

export interface CobrarProyectoBody {
  fecha_cobro: string
  cuenta_id?: string | null
  metodo_pago?: string | null
  referencia_pago?: string | null
}

export const listasPrecioService = {
  async listar(): Promise<ListaPrecio[]> {
    const res = await api.get<ListaPrecio[]>('/listas-precio')
    return res.data
  },

  async obtener(id: string): Promise<ListaPrecioDetail> {
    const res = await api.get<ListaPrecioDetail>(`/listas-precio/${id}`)
    return res.data
  },

  async crear(data: { nombre: string; descripcion?: string }): Promise<ListaPrecio> {
    const res = await api.post<ListaPrecio>('/listas-precio', data)
    return res.data
  },

  async actualizar(
    id: string,
    data: { nombre?: string; descripcion?: string | null },
  ): Promise<ListaPrecio> {
    const res = await api.put<ListaPrecio>(`/listas-precio/${id}`, data)
    return res.data
  },

  async eliminar(id: string): Promise<void> {
    await api.delete(`/listas-precio/${id}`)
  },

  async setearPrecios(id: string, items: PrecioBulkItem[]): Promise<ListaPrecioDetail> {
    const res = await api.put<ListaPrecioDetail>(`/listas-precio/${id}/precios`, { items })
    return res.data
  },

  async getTotalesProyectos(): Promise<TotalProyectoItem[]> {
    const res = await api.get<TotalProyectoItem[]>('/listas-precio/finanzas/totales-proyectos')
    return res.data
  },

  async getDetallePresupuestoProyecto(
    proyectoId: string,
  ): Promise<DetallePresupuestoProyecto> {
    const res = await api.get<DetallePresupuestoProyecto>(
      `/listas-precio/finanzas/totales-proyectos/${proyectoId}/detalle`,
    )
    return res.data
  },

  async getFacturacionProyectos(
    estado?: EstadoFacturacion,
  ): Promise<FacturacionProyectoItem[]> {
    const res = await api.get<FacturacionProyectoItem[]>(
      '/listas-precio/finanzas/facturacion',
      { params: estado ? { estado } : undefined },
    )
    return res.data
  },

  async marcarFacturado(
    proyectoId: string,
    data: FacturarProyectoBody,
  ): Promise<FacturacionProyectoItem> {
    const res = await api.patch<FacturacionProyectoItem>(
      `/listas-precio/finanzas/facturacion/${proyectoId}/facturar`,
      data,
    )
    return res.data
  },

  async marcarCobrado(
    proyectoId: string,
    data: CobrarProyectoBody,
  ): Promise<FacturacionProyectoItem> {
    const res = await api.patch<FacturacionProyectoItem>(
      `/listas-precio/finanzas/facturacion/${proyectoId}/cobrar`,
      data,
    )
    return res.data
  },

  async revertirFacturacion(proyectoId: string): Promise<FacturacionProyectoItem> {
    const res = await api.patch<FacturacionProyectoItem>(
      `/listas-precio/finanzas/facturacion/${proyectoId}/revertir`,
    )
    return res.data
  },

  async descargarPdfFacturacion(proyectoId: string): Promise<Blob> {
    const res = await api.get<Blob>(
      `/listas-precio/finanzas/facturacion/${proyectoId}/pdf`,
      { responseType: 'blob' },
    )
    return res.data
  },
}
