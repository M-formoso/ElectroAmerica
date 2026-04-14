import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Loader2,
  Clock,
  Truck,
  MapPin,
  Package,
  User,
  Eye,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Calendar,
} from 'lucide-react'
import { jornadasOperarioService, type JornadaOperario, type JornadaOperarioList, type EstadoJornada } from '@/services/jornadasOperario'
import { proyectosService } from '@/services/proyectos'

const estadoConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  planificada: { label: 'Planificada', color: 'bg-gray-100 text-gray-800', icon: <Calendar className="h-3 w-3" /> },
  iniciada: { label: 'Iniciada', color: 'bg-yellow-100 text-yellow-800', icon: <Clock className="h-3 w-3" /> },
  en_camino: { label: 'En camino', color: 'bg-blue-100 text-blue-800', icon: <Truck className="h-3 w-3" /> },
  en_obra: { label: 'En obra', color: 'bg-green-100 text-green-800', icon: <CheckCircle2 className="h-3 w-3" /> },
  finalizada: { label: 'Finalizada', color: 'bg-gray-100 text-gray-800', icon: <CheckCircle2 className="h-3 w-3" /> },
  cancelada: { label: 'Cancelada', color: 'bg-red-100 text-red-800', icon: <AlertTriangle className="h-3 w-3" /> },
}

export default function MonitorJornadas() {
  const [fecha, setFecha] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [proyectoFiltro, setProyectoFiltro] = useState<string>('__all__')
  const [estadoFiltro, setEstadoFiltro] = useState<string>('__all__')
  const [jornadaSeleccionada, setJornadaSeleccionada] = useState<JornadaOperario | null>(null)
  const [loadingDetalle, setLoadingDetalle] = useState(false)

  // Cargar jornadas del día
  const { data: jornadas, isLoading, refetch } = useQuery({
    queryKey: ['monitor-jornadas', fecha, proyectoFiltro, estadoFiltro],
    queryFn: () =>
      jornadasOperarioService.getJornadas({
        fecha,
        proyecto_id: proyectoFiltro !== '__all__' ? proyectoFiltro : undefined,
        estado: estadoFiltro !== '__all__' ? (estadoFiltro as EstadoJornada) : undefined,
      }),
    refetchInterval: 30000, // Refresh cada 30 segundos
  })

  // Cargar proyectos para filtro
  const { data: proyectos } = useQuery({
    queryKey: ['proyectos-filtro'],
    queryFn: () => proyectosService.getProyectos(),
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

  // Agrupar por estado para estadísticas
  const estadisticas = jornadas?.reduce(
    (acc, j) => {
      acc[j.estado] = (acc[j.estado] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  const jornadasActivas = jornadas?.filter(j =>
    ['iniciada', 'en_camino', 'en_obra'].includes(j.estado)
  )

  const jornadasFinalizadas = jornadas?.filter(j =>
    ['finalizada', 'cancelada'].includes(j.estado)
  )

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Monitor de Jornadas</h1>
          <p className="text-gray-500">Seguimiento en tiempo real de las jornadas de operarios</p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold">{jornadas?.length || 0}</div>
            <p className="text-sm text-gray-500">Total del día</p>
          </CardContent>
        </Card>
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-yellow-700">{estadisticas?.iniciada || 0}</div>
            <p className="text-sm text-yellow-600">Iniciadas</p>
          </CardContent>
        </Card>
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-blue-700">{estadisticas?.en_camino || 0}</div>
            <p className="text-sm text-blue-600">En camino</p>
          </CardContent>
        </Card>
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-green-700">{estadisticas?.en_obra || 0}</div>
            <p className="text-sm text-green-600">En obra</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold">{estadisticas?.finalizada || 0}</div>
            <p className="text-sm text-gray-500">Finalizadas</p>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="space-y-1">
              <label className="text-sm text-gray-500">Fecha</label>
              <Input
                type="date"
                value={fecha}
                onChange={e => setFecha(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm text-gray-500">Proyecto</label>
              <Select value={proyectoFiltro} onValueChange={setProyectoFiltro}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">Todos</SelectItem>
                  {proyectos?.map(p => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-sm text-gray-500">Estado</label>
              <Select value={estadoFiltro} onValueChange={setEstadoFiltro}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">Todos</SelectItem>
                  {Object.entries(estadoConfig).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setFecha(format(new Date(), 'yyyy-MM-dd'))
                  setProyectoFiltro('__all__')
                  setEstadoFiltro('__all__')
                }}
              >
                Limpiar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs de jornadas */}
      <Tabs defaultValue="activas" className="space-y-4">
        <TabsList>
          <TabsTrigger value="activas">
            Activas ({jornadasActivas?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="finalizadas">
            Finalizadas ({jornadasFinalizadas?.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="activas">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-red-600" />
            </div>
          ) : jornadasActivas && jornadasActivas.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {jornadasActivas.map(jornada => {
                const config = estadoConfig[jornada.estado]
                return (
                  <Card key={jornada.id} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                          <User className="h-4 w-4" />
                          {jornada.operario_nombre}
                        </CardTitle>
                        <Badge className={`${config.color} flex items-center gap-1`}>
                          {config.icon}
                          {config.label}
                        </Badge>
                      </div>
                      <CardDescription className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {jornada.proyecto_nombre}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        {jornada.vehiculo_patente && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Truck className="h-4 w-4" />
                            <span>{jornada.vehiculo_patente}</span>
                          </div>
                        )}
                        {jornada.hora_inicio && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Clock className="h-4 w-4" />
                            <span>Inicio: {format(new Date(jornada.hora_inicio), 'HH:mm')}</span>
                          </div>
                        )}
                        {jornada.hora_llegada_obra && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <CheckCircle2 className="h-4 w-4 text-green-600" />
                            <span>Llegó: {format(new Date(jornada.hora_llegada_obra), 'HH:mm')}</span>
                          </div>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-4"
                        onClick={() => handleVerDetalle(jornada.id)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Ver detalle
                      </Button>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          ) : (
            <Card className="text-center py-12">
              <CardContent>
                <Clock className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">No hay jornadas activas</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="finalizadas">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-red-600" />
            </div>
          ) : jornadasFinalizadas && jornadasFinalizadas.length > 0 ? (
            <div className="space-y-3">
              {jornadasFinalizadas.map(jornada => {
                const config = estadoConfig[jornada.estado]
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
                            <User className="h-4 w-4 text-gray-400" />
                            <span className="font-medium">{jornada.operario_nombre}</span>
                            <Badge className={config.color}>{config.label}</Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {jornada.proyecto_nombre}
                            </span>
                            {jornada.hora_inicio && jornada.hora_fin && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {format(new Date(jornada.hora_inicio), 'HH:mm')} -{' '}
                                {format(new Date(jornada.hora_fin), 'HH:mm')}
                              </span>
                            )}
                            {jornada.km_recorridos && (
                              <span>{jornada.km_recorridos} km</span>
                            )}
                          </div>
                        </div>
                        <Eye className="h-5 w-5 text-gray-400" />
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          ) : (
            <Card className="text-center py-12">
              <CardContent>
                <CheckCircle2 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">No hay jornadas finalizadas en esta fecha</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

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
                <DialogTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  {jornadaSeleccionada.operario_nombre}
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
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  )
}
