// User types
export type RolUsuario = 'administrador' | 'supervisor' | 'operario' | 'cliente'

export interface Usuario {
  id: string
  email: string
  nombre: string
  apellido: string
  telefono?: string
  rol: RolUsuario
  activo: boolean
  created_at: string
  modulos_permitidos?: string[] | null
  es_superadmin: boolean
}

// Auth types
export interface LoginCredentials {
  username: string
  password: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

// Project types
export type EstadoProyecto = 'planificacion' | 'en_ejecucion' | 'pausado' | 'finalizado'

export interface Proyecto {
  id: string
  nombre: string
  descripcion?: string
  ubicacion?: string
  fecha_inicio?: string
  fecha_fin_estimada?: string
  fecha_fin_real?: string
  estado: EstadoProyecto
  porcentaje_avance: number
  monto_contratado?: number
  cliente_id?: string
  cliente_nombre?: string
  supervisor_id?: string
  supervisor?: Usuario
  deposito_id?: string | null
  deposito_nombre?: string
  lista_precio_id?: string | null
  lista_precio_nombre?: string | null
  activo: boolean
  created_at: string
}

// Stage types
export type EstadoEtapa = 'pendiente' | 'en_progreso' | 'completada' | 'pausada'

export interface Etapa {
  id: string
  nombre: string
  descripcion?: string
  orden: number
  fecha_inicio_est?: string
  fecha_fin_est?: string
  fecha_inicio_real?: string
  fecha_fin_real?: string
  estado: EstadoEtapa
  porcentaje_avance: number
  proyecto_id: string
  activo: boolean
}

// Work item types
export interface ItemTrabajo {
  id: string
  nombre: string
  descripcion?: string
  unidad: string
  cantidad_estimada: number
  cantidad_ejecutada: number
  precio_unitario?: number
  etapa_id: string
  activo: boolean
}

// Material types
export interface Material {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  unidad: string
  stock_actual: number
  stock_minimo: number
  precio_unitario?: number
  ubicacion_almacen?: string
  activo: boolean
}

// Equipment types
export type EstadoEquipo = 'disponible' | 'asignado' | 'mantenimiento' | 'fuera_servicio'
export type TipoEquipo = 'herramienta' | 'vehiculo' | 'maquinaria' | 'otro'

export interface Equipo {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  tipo: TipoEquipo
  marca?: string
  modelo?: string
  patente?: string
  estado: EstadoEquipo
  fecha_adquisicion?: string
  costo_adquisicion?: number
  activo: boolean
}

// Expense types
export interface CategoriaGasto {
  id: string
  nombre: string
  descripcion?: string
  color?: string
  activo: boolean
}

export interface Gasto {
  id: string
  descripcion: string
  monto: number
  fecha: string
  comprobante_url?: string
  numero_comprobante?: string
  proyecto_id?: string
  categoria_id?: string
  creado_por_id: string
  proyecto?: Proyecto
  categoria?: CategoriaGasto
  creador?: Usuario
  activo: boolean
  created_at: string
}

// Photo types
export interface Foto {
  id: string
  url: string
  thumbnail_url?: string
  descripcion?: string
  fecha: string
  visible_cliente: boolean
  proyecto_id: string
  etapa_id?: string
  proyecto?: Proyecto
  activo: boolean
  created_at: string
}

// Dashboard types
export interface DashboardResumen {
  proyectos: {
    activos: number
    por_estado: Record<string, number>
  }
  materiales: {
    stock_bajo: number
  }
  equipos: {
    disponibles: number
    asignados: number
    mantenimiento: number
  }
  gastos: {
    mes_actual: number
    mes_anterior: number
    variacion_porcentaje: number
  }
}

export interface Alerta {
  tipo: string
  severidad: 'info' | 'warning' | 'error'
  mensaje: string
  recurso_id: string
  recurso_tipo: string
  proyecto_id?: string
}

// Financial types
export interface ResumenFinancieroProyecto {
  proyecto_id: string
  nombre_proyecto: string
  monto_contratado?: number
  costo_materiales: number
  costo_mano_obra: number
  otros_gastos: number
  costo_total: number
  rentabilidad?: number
  porcentaje_rentabilidad?: number
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ApiError {
  detail: string
}
