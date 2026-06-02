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
}
