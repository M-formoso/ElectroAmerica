import * as React from "react"
import { cn } from "@/lib/utils"
import { format, differenceInDays, isAfter, isBefore, isWithinInterval } from "date-fns"
import { es } from "date-fns/locale"

export interface TimelineItem {
  id: string
  nombre: string
  fecha_inicio_est?: string | null
  fecha_fin_est?: string | null
  fecha_inicio_real?: string | null
  fecha_fin_real?: string | null
  porcentaje_avance: number
  estado: string
  color?: string | null
  sub_items?: TimelineItem[]
}

interface TimelineProps {
  items: TimelineItem[]
  fechaInicio?: string
  fechaFin?: string
  className?: string
  showLegend?: boolean
}

const estadoColors: Record<string, string> = {
  pendiente: "bg-gray-400",
  en_progreso: "bg-blue-500",
  completada: "bg-green-500",
  pausada: "bg-amber-500",
}

const getEstadoColor = (estado: string, customColor?: string | null): string => {
  if (customColor) return ""
  return estadoColors[estado] || "bg-gray-400"
}

export function Timeline({ items, fechaInicio, fechaFin, className, showLegend = true }: TimelineProps) {
  // Calcular rango de fechas
  const allDates: Date[] = []

  items.forEach(item => {
    if (item.fecha_inicio_est) allDates.push(new Date(item.fecha_inicio_est))
    if (item.fecha_fin_est) allDates.push(new Date(item.fecha_fin_est))
    if (item.fecha_inicio_real) allDates.push(new Date(item.fecha_inicio_real))
    if (item.fecha_fin_real) allDates.push(new Date(item.fecha_fin_real))
  })

  if (fechaInicio) allDates.push(new Date(fechaInicio))
  if (fechaFin) allDates.push(new Date(fechaFin))

  if (allDates.length === 0) {
    return (
      <div className={cn("text-center py-8 text-muted-foreground", className)}>
        No hay fechas definidas para mostrar el timeline
      </div>
    )
  }

  const minDate = new Date(Math.min(...allDates.map(d => d.getTime())))
  const maxDate = new Date(Math.max(...allDates.map(d => d.getTime())))
  const totalDays = differenceInDays(maxDate, minDate) || 1
  const today = new Date()

  const calculatePosition = (date: Date): number => {
    const days = differenceInDays(date, minDate)
    return (days / totalDays) * 100
  }

  // Generar marcadores de meses
  const monthMarkers: { date: Date; position: number }[] = []
  let currentDate = new Date(minDate.getFullYear(), minDate.getMonth(), 1)

  while (isBefore(currentDate, maxDate) || currentDate.getMonth() === maxDate.getMonth()) {
    if (isAfter(currentDate, minDate) || currentDate.getMonth() === minDate.getMonth()) {
      monthMarkers.push({
        date: new Date(currentDate),
        position: calculatePosition(currentDate)
      })
    }
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1)
    if (monthMarkers.length > 24) break // Limitar a 24 meses
  }

  const todayPosition = isWithinInterval(today, { start: minDate, end: maxDate })
    ? calculatePosition(today)
    : null

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header con meses */}
      <div className="relative h-8 border-b">
        {monthMarkers.map((marker, idx) => (
          <div
            key={idx}
            className="absolute top-0 -translate-x-1/2 text-xs text-muted-foreground"
            style={{ left: `${marker.position}%` }}
          >
            {format(marker.date, "MMM yy", { locale: es })}
          </div>
        ))}

        {/* Linea de hoy */}
        {todayPosition !== null && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
            style={{ left: `${todayPosition}%` }}
          >
            <div className="absolute -top-4 -translate-x-1/2 text-xs text-red-500 font-medium whitespace-nowrap">
              Hoy
            </div>
          </div>
        )}
      </div>

      {/* Items del timeline */}
      <div className="space-y-3">
        {items.map((item) => {
          const startEst = item.fecha_inicio_est ? new Date(item.fecha_inicio_est) : null
          const endEst = item.fecha_fin_est ? new Date(item.fecha_fin_est) : null
          const startReal = item.fecha_inicio_real ? new Date(item.fecha_inicio_real) : null
          const endReal = item.fecha_fin_real ? new Date(item.fecha_fin_real) : null

          const barStartEst = startEst ? calculatePosition(startEst) : 0
          const barEndEst = endEst ? calculatePosition(endEst) : 100
          const barWidthEst = barEndEst - barStartEst

          const barStartReal = startReal ? calculatePosition(startReal) : barStartEst
          const barEndReal = endReal ? calculatePosition(endReal) : barEndEst
          const barWidthReal = barEndReal - barStartReal

          // Determinar si hay retraso
          const isDelayed = endEst && !endReal && isAfter(today, endEst) && item.estado !== 'completada'

          return (
            <div key={item.id} className="group">
              <div className="flex items-center gap-3">
                {/* Nombre del item */}
                <div className="w-32 flex-shrink-0">
                  <span className="text-sm font-medium truncate block" title={item.nombre}>
                    {item.nombre}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {item.porcentaje_avance.toFixed(0)}%
                  </span>
                </div>

                {/* Barra del timeline */}
                <div className="flex-1 relative h-8">
                  {/* Fondo */}
                  <div className="absolute inset-0 bg-muted rounded" />

                  {/* Barra estimada (fondo claro) */}
                  {startEst && endEst && (
                    <div
                      className={cn(
                        "absolute top-1 bottom-1 rounded opacity-30",
                        getEstadoColor(item.estado, item.color)
                      )}
                      style={{
                        left: `${barStartEst}%`,
                        width: `${barWidthEst}%`,
                        backgroundColor: item.color || undefined
                      }}
                    />
                  )}

                  {/* Barra de progreso real */}
                  <div
                    className={cn(
                      "absolute top-1 bottom-1 rounded transition-all",
                      getEstadoColor(item.estado, item.color),
                      isDelayed && "border-2 border-red-500"
                    )}
                    style={{
                      left: `${barStartReal}%`,
                      width: `${(barWidthReal * item.porcentaje_avance) / 100}%`,
                      backgroundColor: item.color || undefined
                    }}
                  />

                  {/* Indicador de retraso */}
                  {isDelayed && (
                    <div
                      className="absolute top-1 bottom-1 bg-red-200 border-l-2 border-red-500 rounded-r"
                      style={{
                        left: `${barEndEst}%`,
                        width: `${calculatePosition(today) - barEndEst}%`
                      }}
                    />
                  )}

                  {/* Linea de hoy */}
                  {todayPosition !== null && (
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-red-500"
                      style={{ left: `${todayPosition}%` }}
                    />
                  )}

                  {/* Tooltip on hover */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 bg-popover border rounded-md shadow-lg p-2 text-xs z-20 whitespace-nowrap">
                      <div className="font-medium">{item.nombre}</div>
                      {startEst && <div>Inicio Est: {format(startEst, "dd/MM/yy")}</div>}
                      {endEst && <div>Fin Est: {format(endEst, "dd/MM/yy")}</div>}
                      {startReal && <div>Inicio Real: {format(startReal, "dd/MM/yy")}</div>}
                      {endReal && <div>Fin Real: {format(endReal, "dd/MM/yy")}</div>}
                      <div>Avance: {item.porcentaje_avance.toFixed(0)}%</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sub-items (sub-etapas) */}
              {item.sub_items && item.sub_items.length > 0 && (
                <div className="ml-8 mt-2 space-y-2 border-l-2 pl-4">
                  {item.sub_items.map((subItem) => {
                    const subStartEst = subItem.fecha_inicio_est ? new Date(subItem.fecha_inicio_est) : null
                    const subEndEst = subItem.fecha_fin_est ? new Date(subItem.fecha_fin_est) : null
                    const subBarStartEst = subStartEst ? calculatePosition(subStartEst) : 0
                    const subBarEndEst = subEndEst ? calculatePosition(subEndEst) : 100
                    const subBarWidthEst = subBarEndEst - subBarStartEst

                    return (
                      <div key={subItem.id} className="flex items-center gap-3">
                        <div className="w-24 flex-shrink-0">
                          <span className="text-xs truncate block" title={subItem.nombre}>
                            {subItem.nombre}
                          </span>
                        </div>
                        <div className="flex-1 relative h-5">
                          <div className="absolute inset-0 bg-muted/50 rounded" />
                          <div
                            className={cn(
                              "absolute top-0.5 bottom-0.5 rounded",
                              getEstadoColor(subItem.estado, subItem.color)
                            )}
                            style={{
                              left: `${subBarStartEst}%`,
                              width: `${(subBarWidthEst * subItem.porcentaje_avance) / 100}%`,
                              backgroundColor: subItem.color || undefined
                            }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Leyenda */}
      {showLegend && (
        <div className="flex flex-wrap gap-4 pt-4 border-t">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-gray-400" />
            <span className="text-xs">Pendiente</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-500" />
            <span className="text-xs">En Progreso</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-500" />
            <span className="text-xs">Completada</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-amber-500" />
            <span className="text-xs">Pausada</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-2 rounded bg-red-200 border border-red-500" />
            <span className="text-xs">Retraso</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-0.5 h-4 bg-red-500" />
            <span className="text-xs">Hoy</span>
          </div>
        </div>
      )}
    </div>
  )
}

// Componente simplificado para mostrar progreso de etapas
interface EtapasProgressProps {
  etapas: Array<{
    id: string
    nombre: string
    porcentaje_avance: number
    estado: string
    color?: string | null
  }>
  className?: string
}

export function EtapasProgress({ etapas, className }: EtapasProgressProps) {
  const totalAvance = etapas.length > 0
    ? etapas.reduce((sum, e) => sum + e.porcentaje_avance, 0) / etapas.length
    : 0

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium">Avance por Etapas</span>
        <span className="text-sm font-bold">{totalAvance.toFixed(0)}%</span>
      </div>

      {/* Barra combinada */}
      <div className="h-6 bg-muted rounded-full overflow-hidden flex">
        {etapas.map((etapa, idx) => {
          const width = 100 / etapas.length
          const fillWidth = (width * etapa.porcentaje_avance) / 100

          return (
            <div
              key={etapa.id}
              className="relative h-full"
              style={{ width: `${width}%` }}
              title={`${etapa.nombre}: ${etapa.porcentaje_avance.toFixed(0)}%`}
            >
              <div
                className={cn(
                  "absolute inset-y-0 left-0 transition-all",
                  getEstadoColor(etapa.estado, etapa.color)
                )}
                style={{
                  width: `${(etapa.porcentaje_avance / 100) * 100}%`,
                  backgroundColor: etapa.color || undefined
                }}
              />
              {idx > 0 && (
                <div className="absolute left-0 top-0 bottom-0 w-px bg-background" />
              )}
            </div>
          )
        })}
      </div>

      {/* Lista de etapas */}
      <div className="grid grid-cols-2 gap-2">
        {etapas.map((etapa) => (
          <div key={etapa.id} className="flex items-center gap-2 text-xs">
            <div
              className={cn(
                "w-3 h-3 rounded",
                getEstadoColor(etapa.estado, etapa.color)
              )}
              style={{ backgroundColor: etapa.color || undefined }}
            />
            <span className="truncate flex-1">{etapa.nombre}</span>
            <span className="font-medium">{etapa.porcentaje_avance.toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
