import api from './api'

export interface DatosReporte {
  proyecto: {
    id: string
    nombre: string
    descripcion?: string
    ubicacion?: string
    estado: string
    porcentaje_avance: number
    fecha_inicio?: string
    fecha_fin_estimada?: string
    fecha_fin_real?: string
    monto_contratado?: number
    cliente?: {
      nombre: string
      email: string
      telefono?: string
    }
    supervisor?: {
      nombre: string
      email: string
      telefono?: string
    }
  }
  periodo: {
    desde: string
    hasta: string
  }
  resumen: {
    total_etapas: number
    etapas_completadas: number
    total_materiales_asignados: number
    costo_materiales: number
    total_equipos_usados: number
    total_gastos: number
    gastos_por_categoria: Record<string, number>
    total_fotos: number
  }
  etapas: Array<{
    id: string
    nombre: string
    descripcion?: string
    estado: string
    porcentaje_avance: number
    fecha_inicio_est?: string
    fecha_fin_est?: string
    fecha_inicio_real?: string
    fecha_fin_real?: string
    items: Array<{
      id: string
      nombre: string
      descripcion?: string
      unidad: string
      cantidad_estimada: number
      cantidad_ejecutada: number
      porcentaje: number
      precio_unitario?: number
    }>
    items_total: number
  }>
  materiales: Array<{
    nombre: string
    codigo: string
    cantidad: number
    unidad: string
    fecha: string
    etapa: string
    notas?: string
    costo_estimado?: number
  }>
  equipos: Array<{
    nombre: string
    codigo: string
    tipo: string
    marca?: string
    modelo?: string
    fecha_asignacion: string
    fecha_devolucion_est?: string
    fecha_devolucion_real?: string
    notas?: string
  }>
  gastos: Array<{
    id: string
    fecha: string
    categoria: string
    descripcion: string
    monto: number
    comprobante_url?: string
    numero_comprobante?: string
  }>
  fotos: Array<{
    id: string
    url: string
    thumbnail_url?: string
    descripcion?: string
    fecha: string
    etapa: string
    visible_cliente: boolean
  }>
}

export interface Reporte {
  id: string
  proyecto_id: string
  tipo: string
  fecha_desde: string
  fecha_hasta: string
  pdf_url?: string
  excel_url?: string
  compartido_cliente: boolean
  created_at: string
}

export const reportesService = {
  getDatosReporte: async (
    proyectoId: string,
    fechaDesde: string,
    fechaHasta: string
  ): Promise<DatosReporte> => {
    const response = await api.get(`/reportes/proyecto/${proyectoId}`, {
      params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta }
    })
    return response.data
  },

  getReportesProyecto: async (proyectoId: string, limit: number = 20): Promise<Reporte[]> => {
    const response = await api.get(`/reportes/proyecto/${proyectoId}/listado`, {
      params: { limit }
    })
    return response.data
  },

  generarReporte: async (
    proyectoId: string,
    fechaDesde: string,
    fechaHasta: string
  ): Promise<Reporte> => {
    const response = await api.post(
      `/reportes/proyecto/${proyectoId}/generar`,
      null,
      { params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta } }
    )
    return response.data
  },

  compartirConCliente: async (proyectoId: string, reporteId: string): Promise<void> => {
    await api.post(`/reportes/compartir/${proyectoId}`, { reporte_id: reporteId })
  },

  getUltimoReporteSemanal: async (proyectoId: string): Promise<Reporte> => {
    const response = await api.get(`/reportes/semanal/${proyectoId}`)
    return response.data
  },
}
