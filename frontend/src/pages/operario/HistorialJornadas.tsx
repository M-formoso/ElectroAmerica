import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Loader2, Clock, Truck, MapPin, Package, Calendar, ChevronRight } from 'lucide-react'
import { jornadasOperarioService, type JornadaOperario, type JornadaOperarioList } from '@/services/jornadasOperario'

const estadoConfig: Record<string, { label: string; color: string }> = {
  planificada: { label: 'Planificada', color: 'bg-gray-100 text-gray-800' },
  iniciada: { label: 'Iniciada', color: 'bg-yellow-100 text-yellow-800' },
  en_camino: { label: 'En camino', color: 'bg-blue-100 text-blue-800' },
  en_obra: { label: 'En obra', color: 'bg-green-100 text-green-800' },
  finalizada: { label: 'Finalizada', color: 'bg-gray-100 text-gray-800' },
  cancelada: { label: 'Cancelada', color: 'bg-red-100 text-red-800' },
}

export default function HistorialJornadas() {
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [jornadaSeleccionada, setJornadaSeleccionada] = useState<JornadaOperario | null>(null)
  const [loadingDetalle, setLoadingDetalle] = useState(false)

  const { data: jornadas, isLoading } = useQuery({
    queryKey: ['mi-historial-jornadas', fechaDesde, fechaHasta],
    queryFn: () =>
      jornadasOperarioService.getMiHistorial({
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
        limit: 50,
      }),
  })

  const handleVerDetalle = async (jornadaId: string) => {
    setLoadingDetalle(true)
    try {
      const detalle = await jornadasOperarioService.getJornada(jornadaId)
      setJornadaSeleccionada(detalle)
    } finally {
      setLoadingDetalle(false)
    }
  }

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Mi Historial de Jornadas</h1>
        <p className="text-gray-500">Revisá tus jornadas anteriores</p>
      </div>

      {/* Filtros */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="space-y-1">
              <label className="text-sm text-gray-500">Desde</label>
              <Input
                type="date"
                value={fechaDesde}
                onChange={e => setFechaDesde(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm text-gray-500">Hasta</label>
              <Input
                type="date"
                value={fechaHasta}
                onChange={e => setFechaHasta(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setFechaDesde('')
                  setFechaHasta('')
                }}
              >
                Limpiar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de jornadas */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-red-600" />
        </div>
      ) : jornadas && jornadas.length > 0 ? (
        <div className="space-y-3">
          {jornadas.map(jornada => {
            const config = estadoConfig[jornada.estado] || estadoConfig.planificada
            return (
              <Card
                key={jornada.id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => handleVerDetalle(jornada.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <span className="font-medium">
                          {format(new Date(jornada.fecha), "EEEE d 'de' MMMM", { locale: es })}
                        </span>
                        <Badge className={config.color}>{config.label}</Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {jornada.proyecto_nombre}
                        </span>
                        {jornada.vehiculo_patente && (
                          <span className="flex items-center gap-1">
                            <Truck className="h-3 w-3" />
                            {jornada.vehiculo_patente}
                          </span>
                        )}
                        {jornada.hora_inicio && jornada.hora_fin && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {format(new Date(jornada.hora_inicio), 'HH:mm')} -{' '}
                            {format(new Date(jornada.hora_fin), 'HH:mm')}
                          </span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <Card className="text-center py-12">
          <CardContent>
            <Clock className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-500">No hay jornadas en el período seleccionado</p>
          </CardContent>
        </Card>
      )}

      {/* Dialog de detalle */}
      <Dialog open={!!jornadaSeleccionada} onOpenChange={() => setJornadaSeleccionada(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {loadingDetalle ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-red-600" />
            </div>
          ) : jornadaSeleccionada ? (
            <>
              <DialogHeader>
                <DialogTitle>
                  Jornada del{' '}
                  {format(new Date(jornadaSeleccionada.fecha), "d 'de' MMMM yyyy", { locale: es })}
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-6">
                {/* Info general */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-sm text-gray-500">Proyecto</p>
                    <p className="font-medium">{jornadaSeleccionada.proyecto_nombre}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-500">Etapa</p>
                    <p className="font-medium">{jornadaSeleccionada.etapa_nombre || '-'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-500">Vehículo</p>
                    <p className="font-medium">{jornadaSeleccionada.vehiculo_patente || '-'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-500">Estado</p>
                    <Badge className={estadoConfig[jornadaSeleccionada.estado]?.color}>
                      {estadoConfig[jornadaSeleccionada.estado]?.label}
                    </Badge>
                  </div>
                </div>

                {/* Horarios */}
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">Horarios</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Inicio</p>
                      <p>
                        {jornadaSeleccionada.hora_inicio
                          ? format(new Date(jornadaSeleccionada.hora_inicio), 'HH:mm')
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Llegada obra</p>
                      <p>
                        {jornadaSeleccionada.hora_llegada_obra
                          ? format(new Date(jornadaSeleccionada.hora_llegada_obra), 'HH:mm')
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Fin</p>
                      <p>
                        {jornadaSeleccionada.hora_fin
                          ? format(new Date(jornadaSeleccionada.hora_fin), 'HH:mm')
                          : '-'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Kilometraje */}
                {(jornadaSeleccionada.km_inicial || jornadaSeleccionada.km_final) && (
                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-3">Kilometraje</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Inicial</p>
                        <p>{jornadaSeleccionada.km_inicial || '-'} km</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Final</p>
                        <p>{jornadaSeleccionada.km_final || '-'} km</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Recorrido</p>
                        <p>{jornadaSeleccionada.km_recorridos || '-'} km</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Materiales */}
                {jornadaSeleccionada.materiales && jornadaSeleccionada.materiales.length > 0 && (
                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <Package className="h-4 w-4" />
                      Materiales
                    </h4>
                    <div className="space-y-2">
                      {jornadaSeleccionada.materiales.map(mat => (
                        <div
                          key={mat.id}
                          className="flex justify-between items-center p-2 bg-gray-50 rounded"
                        >
                          <div>
                            <p className="font-medium text-sm">{mat.material_nombre}</p>
                            <p className="text-xs text-gray-500">
                              Cargado: {mat.cantidad_cargada} | Consumido: {mat.cantidad_consumida || 0}{' '}
                              | Devuelto: {mat.cantidad_devuelta || 0}
                            </p>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {mat.estado.replace('_', ' ')}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Novedades */}
                {jornadaSeleccionada.novedades && (
                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-3">Novedades</h4>
                    <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded">
                      {jornadaSeleccionada.novedades}
                    </pre>
                  </div>
                )}

                {/* Observaciones */}
                {(jornadaSeleccionada.observaciones_inicio ||
                  jornadaSeleccionada.observaciones_cierre) && (
                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-3">Observaciones</h4>
                    {jornadaSeleccionada.observaciones_inicio && (
                      <div className="mb-2">
                        <p className="text-xs text-gray-500">Al inicio:</p>
                        <p className="text-sm">{jornadaSeleccionada.observaciones_inicio}</p>
                      </div>
                    )}
                    {jornadaSeleccionada.observaciones_cierre && (
                      <div>
                        <p className="text-xs text-gray-500">Al cierre:</p>
                        <p className="text-sm">{jornadaSeleccionada.observaciones_cierre}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  )
}
