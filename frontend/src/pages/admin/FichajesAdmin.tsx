import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Clock, Users, CheckCircle, Timer, Search, RefreshCw } from 'lucide-react'
import { fichajesService } from '@/services/fichajes'
import type { EstadoFichaje, FichajeListItem } from '@/services/fichajes'
import { cn } from '@/lib/utils'

function formatHora(iso: string) {
  return new Date(iso).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
}

function formatFechaCorta(iso: string) {
  return new Date(iso).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function estadoBadge(estado: EstadoFichaje) {
  const styles: Record<EstadoFichaje, string> = {
    activo: 'bg-green-100 text-green-800',
    completado: 'bg-blue-100 text-blue-800',
    cancelado: 'bg-gray-100 text-gray-600',
  }
  const labels: Record<EstadoFichaje, string> = {
    activo: 'Activo',
    completado: 'Completado',
    cancelado: 'Cancelado',
  }
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', styles[estado])}>
      {labels[estado]}
    </span>
  )
}

export default function FichajesAdminPage() {
  const today = new Date().toISOString().split('T')[0]
  const [fechaDesde, setFechaDesde] = useState(today)
  const [fechaHasta, setFechaHasta] = useState(today)
  const [estadoFiltro, setEstadoFiltro] = useState<string>('todos')
  const [busqueda, setBusqueda] = useState('')

  const params = {
    fecha_desde: fechaDesde || undefined,
    fecha_hasta: fechaHasta || undefined,
    estado: estadoFiltro !== 'todos' ? (estadoFiltro as EstadoFichaje) : undefined,
  }

  const { data: fichajes = [], isLoading, refetch } = useQuery({
    queryKey: ['fichajes-admin', params],
    queryFn: () => fichajesService.listar(params),
    refetchInterval: 60_000,
  })

  const { data: resumen } = useQuery({
    queryKey: ['fichajes-resumen', params],
    queryFn: () => fichajesService.resumen(params),
  })

  const filtrados = fichajes.filter((f: FichajeListItem) => {
    if (!busqueda) return true
    const nombre = `${f.operario_nombre ?? ''} ${f.operario_apellido ?? ''}`.toLowerCase()
    return nombre.includes(busqueda.toLowerCase())
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Fichajes</h1>
          <p className="text-muted-foreground">Control de entradas y salidas de operarios</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-1" />
          Actualizar
        </Button>
      </div>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <Users className="h-8 w-8 text-muted-foreground" />
                <div>
                  <p className="text-2xl font-bold">{resumen.total_fichajes}</p>
                  <p className="text-xs text-muted-foreground">Total fichajes</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-green-200">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <Clock className="h-8 w-8 text-green-600" />
                <div>
                  <p className="text-2xl font-bold text-green-600">{resumen.fichajes_activos}</p>
                  <p className="text-xs text-muted-foreground">En jornada ahora</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-8 w-8 text-blue-600" />
                <div>
                  <p className="text-2xl font-bold">{resumen.fichajes_completados}</p>
                  <p className="text-xs text-muted-foreground">Completados</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <Timer className="h-8 w-8 text-muted-foreground" />
                <div>
                  <p className="text-2xl font-bold">{Number(resumen.horas_totales).toFixed(1)}hs</p>
                  <p className="text-xs text-muted-foreground">Horas totales</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtros */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Desde</label>
              <Input type="date" value={fechaDesde} onChange={(e) => setFechaDesde(e.target.value)} />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Hasta</label>
              <Input type="date" value={fechaHasta} onChange={(e) => setFechaHasta(e.target.value)} />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Estado</label>
              <Select value={estadoFiltro} onValueChange={setEstadoFiltro}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="activo">Activos</SelectItem>
                  <SelectItem value="completado">Completados</SelectItem>
                  <SelectItem value="cancelado">Cancelados</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Buscar operario</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Nombre..."
                  className="pl-8"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla */}
      <Card>
        <CardContent className="pt-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Clock className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filtrados.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Clock className="h-10 w-10 mx-auto mb-3 opacity-30" />
              <p>No hay fichajes en el período seleccionado</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-3 pr-4 font-medium">Operario</th>
                    <th className="py-3 pr-4 font-medium">Fecha</th>
                    <th className="py-3 pr-4 font-medium">Entrada</th>
                    <th className="py-3 pr-4 font-medium">Salida</th>
                    <th className="py-3 pr-4 font-medium">Horas</th>
                    <th className="py-3 pr-4 font-medium">Proyecto</th>
                    <th className="py-3 font-medium">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {filtrados.map((f: FichajeListItem) => (
                    <tr key={f.id} className="border-b last:border-0 hover:bg-muted/30">
                      <td className="py-3 pr-4 font-medium">
                        {f.operario_nombre} {f.operario_apellido}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">{formatFechaCorta(f.fecha)}</td>
                      <td className="py-3 pr-4 font-mono">{formatHora(f.hora_inicio)}</td>
                      <td className="py-3 pr-4 font-mono text-muted-foreground">
                        {f.hora_fin ? formatHora(f.hora_fin) : '—'}
                      </td>
                      <td className="py-3 pr-4">
                        {f.horas_trabajadas != null ? (
                          <span className="font-medium">{Number(f.horas_trabajadas).toFixed(2)}hs</span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {f.proyecto_nombre ?? '—'}
                      </td>
                      <td className="py-3">{estadoBadge(f.estado)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
