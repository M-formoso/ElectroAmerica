import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Clock, Users, CheckCircle, Timer, Search, RefreshCw, LogIn, LogOut, UserCog, FileDown, Trash2, Calendar } from 'lucide-react'
import { fichajesService } from '@/services/fichajes'
import type { EstadoFichaje, FichajeListItem } from '@/services/fichajes'
import { usuariosService } from '@/services/usuarios'
import type { Usuario } from '@/services/usuarios'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

function formatHora(iso: string) {
  return new Date(iso).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
}

function horaActual() {
  const now = new Date()
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}

function fechaHoy() {
  return new Date().toISOString().split('T')[0]
}

function primerDiaMes() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

function fechaDeIso(iso: string) {
  return new Date(iso).toISOString().split('T')[0]
}

function formatFechaCorta(iso: string) {
  return new Date(iso).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function estadoBadge(estado: EstadoFichaje) {
  const styles: Record<EstadoFichaje, string> = {
    activo: 'bg-green-100 text-green-800',
    completado: 'bg-blue-100 text-blue-800',
    cancelado: 'bg-gray-100 text-gray-600',
    inasistencia: 'bg-orange-100 text-orange-800',
  }
  const labels: Record<EstadoFichaje, string> = {
    activo: 'Activo',
    completado: 'Completado',
    cancelado: 'Cancelado',
    inasistencia: 'Faltó',
  }
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', styles[estado])}>
      {labels[estado]}
    </span>
  )
}

export default function FichajesAdminPage() {
  const { toast } = useToast()
  const qc = useQueryClient()
  const today = new Date().toISOString().split('T')[0]
  const [fechaDesde, setFechaDesde] = useState(primerDiaMes())
  const [fechaHasta, setFechaHasta] = useState(today)
  const [estadoFiltro, setEstadoFiltro] = useState<string>('todos')
  const [busqueda, setBusqueda] = useState('')

  const [descargandoPdf, setDescargandoPdf] = useState(false)
  const [fichajeABorrar, setFichajeABorrar] = useState<FichajeListItem | null>(null)
  const [mostrarSugerencias, setMostrarSugerencias] = useState(false)

  // Dialog fichar por operario
  const [showFicharDialog, setShowFicharDialog] = useState(false)
  const [operarioSeleccionado, setOperarioSeleccionado] = useState<string>('')
  const [notas, setNotas] = useState('')
  const [horaEntrada, setHoraEntrada] = useState('')
  const [fechaEntrada, setFechaEntrada] = useState('')
  const [marcarFalto, setMarcarFalto] = useState(false)
  // Dialog fichar salida por admin
  const [showSalidaDialog, setShowSalidaDialog] = useState(false)
  const [fichajeParaSalida, setFichajeParaSalida] = useState<FichajeListItem | null>(null)
  const [notasSalida, setNotasSalida] = useState('')
  const [horaSalida, setHoraSalida] = useState('')
  const [fechaSalida, setFechaSalida] = useState('')

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

  const { data: activos = [] } = useQuery({
    queryKey: ['fichajes-activos'],
    queryFn: () => fichajesService.obtenerActivos(),
    refetchInterval: 30_000,
  })

  const { data: operarios = [] } = useQuery({
    queryKey: ['usuarios-operarios'],
    queryFn: () => usuariosService.getUsuarios({ rol: 'operario' }),
  })

  const fichajeEntradaMutation = useMutation({
    mutationFn: () => fichajesService.ficharEntradaAdmin({
      operario_id: operarioSeleccionado,
      notas_inicio: notas || undefined,
      hora_manual: horaEntrada || undefined,
      fecha_manual: fechaEntrada || undefined,
    }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['fichajes-admin'] })
      qc.invalidateQueries({ queryKey: ['fichajes-activos'] })
      qc.invalidateQueries({ queryKey: ['fichajes-resumen'] })
      setShowFicharDialog(false)
      setOperarioSeleccionado('')
      setNotas('')
      setHoraEntrada('')
      setFechaEntrada('')
      const op = operarios.find((o: Usuario) => o.id === data.operario_id)
      toast({ title: 'Entrada fichada', description: `Fichaje de ${op?.nombre ?? ''} ${op?.apellido ?? ''} registrado.` })
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ title: 'Error', description: detail || 'No se pudo fichar entrada', variant: 'destructive' })
    },
  })

  const inasistenciaMutation = useMutation({
    mutationFn: () => fichajesService.marcarInasistencia({
      operario_id: operarioSeleccionado,
      fecha: fechaEntrada || fechaHoy(),
      motivo: notas || undefined,
    }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['fichajes-admin'] })
      qc.invalidateQueries({ queryKey: ['fichajes-resumen'] })
      setShowFicharDialog(false)
      setOperarioSeleccionado('')
      setNotas('')
      setHoraEntrada('')
      setFechaEntrada('')
      setMarcarFalto(false)
      const op = operarios.find((o: Usuario) => o.id === data.operario_id)
      toast({ title: 'Inasistencia registrada', description: `${op?.nombre ?? ''} ${op?.apellido ?? ''} marcado como ausente.` })
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ title: 'Error', description: detail || 'No se pudo marcar inasistencia', variant: 'destructive' })
    },
  })

  const fichajeSalidaMutation = useMutation({
    mutationFn: () => fichajesService.ficharSalidaAdmin(fichajeParaSalida!.id, {
      notas_fin: notasSalida || undefined,
      hora_manual: horaSalida || undefined,
      fecha_manual: fechaSalida || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fichajes-admin'] })
      qc.invalidateQueries({ queryKey: ['fichajes-activos'] })
      qc.invalidateQueries({ queryKey: ['fichajes-resumen'] })
      setShowSalidaDialog(false)
      setFichajeParaSalida(null)
      setNotasSalida('')
      setHoraSalida('')
      setFechaSalida('')
      toast({ title: 'Salida fichada', description: 'Jornada finalizada correctamente.' })
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ title: 'Error', description: detail || 'No se pudo fichar salida', variant: 'destructive' })
    },
  })

  const borrarMutation = useMutation({
    mutationFn: (id: string) => fichajesService.eliminar(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fichajes-admin'] })
      qc.invalidateQueries({ queryKey: ['fichajes-resumen'] })
      setFichajeABorrar(null)
      toast({ title: 'Fichaje eliminado' })
    },
    onError: () => toast({ title: 'Error al eliminar', variant: 'destructive' }),
  })

  const handleDescargarPdf = async () => {
    setDescargandoPdf(true)
    try {
      const blob = await fichajesService.descargarPdf({
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `fichajes_${fechaDesde || 'todo'}_${fechaHasta || 'hoy'}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast({ title: 'Error al generar PDF', variant: 'destructive' })
    } finally {
      setDescargandoPdf(false)
    }
  }

  const filtrados = fichajes.filter((f: FichajeListItem) => {
    if (!busqueda) return true
    const nombre = `${f.operario_nombre ?? ''} ${f.operario_apellido ?? ''}`.toLowerCase()
    return nombre.includes(busqueda.toLowerCase())
  })

  // Operarios sin fichaje activo (disponibles para fichar entrada)
  const operariosActivosIds = new Set(activos.map((f: FichajeListItem) => f.operario_id))
  const operariosSinFichaje = operarios.filter((o: Usuario) => !operariosActivosIds.has(o.id) && o.activo)

  // Sugerencias para autocomplete del buscador
  const operariosSugeridos = busqueda.trim()
    ? operarios
        .filter((o: Usuario) => o.activo)
        .filter((o: Usuario) => `${o.nombre} ${o.apellido}`.toLowerCase().includes(busqueda.toLowerCase()))
        .slice(0, 8)
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Fichajes</h1>
          <p className="text-muted-foreground">Control de entradas y salidas de operarios</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Actualizar
          </Button>
          <Button variant="outline" size="sm" onClick={handleDescargarPdf} disabled={descargandoPdf}>
            <FileDown className="h-4 w-4 mr-1" />
            {descargandoPdf ? 'Generando...' : 'Descargar PDF'}
          </Button>
          <Button size="sm" onClick={() => setShowFicharDialog(true)}>
            <UserCog className="h-4 w-4 mr-1" />
            Fichar por operario
          </Button>
        </div>
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

      {/* Activos ahora */}
      {activos.length > 0 && (
        <Card className="border-green-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 text-green-700">
              <Clock className="h-4 w-4" />
              En jornada ahora ({activos.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {activos.map((f: FichajeListItem) => (
                <div key={f.id} className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                  <div>
                    <p className="text-sm font-medium">{f.operario_nombre} {f.operario_apellido}</p>
                    <p className="text-xs text-muted-foreground">Desde {formatHora(f.hora_inicio)}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => { setFichajeParaSalida(f); setHoraSalida(horaActual()); setFechaSalida(fechaDeIso(f.hora_inicio)); setShowSalidaDialog(true) }}
                  >
                    <LogOut className="h-3.5 w-3.5 mr-1" />
                    Salida
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
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
                  <SelectItem value="inasistencia">Inasistencias</SelectItem>
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
                  onChange={(e) => { setBusqueda(e.target.value); setMostrarSugerencias(true) }}
                  onFocus={() => setMostrarSugerencias(true)}
                  onBlur={() => setTimeout(() => setMostrarSugerencias(false), 150)}
                />
                {mostrarSugerencias && operariosSugeridos.length > 0 && (
                  <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border rounded-md shadow-lg max-h-56 overflow-y-auto">
                    {operariosSugeridos.map((o: Usuario) => (
                      <button
                        key={o.id}
                        type="button"
                        className="w-full text-left px-3 py-2 text-sm hover:bg-muted flex items-center gap-2"
                        onMouseDown={(e) => {
                          e.preventDefault()
                          setBusqueda(`${o.nombre} ${o.apellido}`)
                          setMostrarSugerencias(false)
                        }}
                      >
                        <Users className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>{o.nombre} {o.apellido}</span>
                      </button>
                    ))}
                  </div>
                )}
                {mostrarSugerencias && busqueda.trim() && operariosSugeridos.length === 0 && (
                  <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border rounded-md shadow-lg px-3 py-2 text-xs text-muted-foreground">
                    Sin operarios que coincidan
                  </div>
                )}
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
                    <th className="py-3 pr-4 font-medium">Estado</th>
                    <th className="py-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {filtrados.map((f: FichajeListItem) => {
                    const esInasistencia = f.estado === 'inasistencia'
                    return (
                      <tr key={f.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="py-3 pr-4 font-medium">
                          {f.operario_nombre} {f.operario_apellido}
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">{formatFechaCorta(f.fecha)}</td>
                        <td className="py-3 pr-4 font-mono">
                          {esInasistencia ? <span className="text-muted-foreground">—</span> : formatHora(f.hora_inicio)}
                        </td>
                        <td className="py-3 pr-4 font-mono text-muted-foreground">
                          {esInasistencia ? '—' : (f.hora_fin ? formatHora(f.hora_fin) : '—')}
                        </td>
                        <td className="py-3 pr-4">
                          {esInasistencia ? (
                            <span className="text-muted-foreground">—</span>
                          ) : f.horas_trabajadas != null ? (
                            <span className="font-medium">{Number(f.horas_trabajadas).toFixed(2)}hs</span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">
                          {f.proyecto_nombre ?? '—'}
                        </td>
                        <td className="py-3 pr-4">{estadoBadge(f.estado)}</td>
                        <td className="py-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 text-muted-foreground hover:text-red-600"
                            onClick={() => setFichajeABorrar(f)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialog: fichar entrada por operario */}
      <Dialog open={showFicharDialog} onOpenChange={(open) => { setShowFicharDialog(open); if (!open) { setOperarioSeleccionado(''); setNotas(''); setHoraEntrada(''); setFechaEntrada(''); setMarcarFalto(false) } else { setHoraEntrada(horaActual()); setFechaEntrada(fechaHoy()) } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCog className="h-5 w-5" />
              {marcarFalto ? 'Marcar inasistencia' : 'Fichar entrada por operario'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {/* Toggle: fichar entrada vs marcar inasistencia */}
            <div className="flex items-center gap-2 p-2 bg-muted/30 rounded-md">
              <Button
                type="button"
                size="sm"
                variant={!marcarFalto ? 'default' : 'ghost'}
                className="flex-1"
                onClick={() => setMarcarFalto(false)}
              >
                <LogIn className="h-4 w-4 mr-2" />
                Fichó
              </Button>
              <Button
                type="button"
                size="sm"
                variant={marcarFalto ? 'default' : 'ghost'}
                className={cn('flex-1', marcarFalto && 'bg-orange-600 hover:bg-orange-700')}
                onClick={() => setMarcarFalto(true)}
              >
                Faltó
              </Button>
            </div>

            <div className="space-y-2">
              <Label>Operario *</Label>
              <Select value={operarioSeleccionado} onValueChange={setOperarioSeleccionado}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccioná un operario..." />
                </SelectTrigger>
                <SelectContent>
                  {marcarFalto ? (
                    operarios.filter((o: Usuario) => o.activo).length === 0 ? (
                      <SelectItem value="__none__" disabled>No hay operarios activos</SelectItem>
                    ) : (
                      operarios.filter((o: Usuario) => o.activo).map((o: Usuario) => (
                        <SelectItem key={o.id} value={o.id}>
                          {o.nombre} {o.apellido}
                        </SelectItem>
                      ))
                    )
                  ) : (
                    operariosSinFichaje.length === 0 ? (
                      <SelectItem value="__none__" disabled>Todos los operarios ya ficharon entrada</SelectItem>
                    ) : (
                      operariosSinFichaje.map((o: Usuario) => (
                        <SelectItem key={o.id} value={o.id}>
                          {o.nombre} {o.apellido}
                        </SelectItem>
                      ))
                    )
                  )}
                </SelectContent>
              </Select>
              {!marcarFalto && operariosActivosIds.size > 0 && (
                <p className="text-xs text-muted-foreground">
                  {operariosActivosIds.size} operario{operariosActivosIds.size > 1 ? 's' : ''} ya {operariosActivosIds.size > 1 ? 'tienen' : 'tiene'} fichaje activo y no aparece{operariosActivosIds.size > 1 ? 'n' : ''} en la lista.
                </p>
              )}
            </div>

            {marcarFalto ? (
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  Fecha de la inasistencia
                </Label>
                <Input
                  type="date"
                  value={fechaEntrada}
                  max={fechaHoy()}
                  onChange={(e) => setFechaEntrada(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">El operario queda registrado como ausente ese día.</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      Fecha
                    </Label>
                    <Input
                      type="date"
                      value={fechaEntrada}
                      max={fechaHoy()}
                      onChange={(e) => setFechaEntrada(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      Hora de entrada
                    </Label>
                    <Input
                      type="time"
                      value={horaEntrada}
                      onChange={(e) => setHoraEntrada(e.target.value)}
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground -mt-2">Pre-cargadas con fecha y hora actuales. Modificalas para cargar un fichaje de un día anterior.</p>
              </>
            )}

            <div className="space-y-2">
              <Label>{marcarFalto ? 'Motivo (opcional)' : 'Notas (opcional)'}</Label>
              <Textarea
                placeholder={marcarFalto ? 'Ej: Aviso por enfermedad' : 'Ej: Fichaje manual — operario olvidó el celular'}
                value={notas}
                onChange={(e) => setNotas(e.target.value)}
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFicharDialog(false)}>Cancelar</Button>
            {marcarFalto ? (
              <Button
                className="bg-orange-600 hover:bg-orange-700"
                onClick={() => inasistenciaMutation.mutate()}
                disabled={!operarioSeleccionado || operarioSeleccionado === '__none__' || inasistenciaMutation.isPending}
              >
                Marcar inasistencia
              </Button>
            ) : (
              <Button
                onClick={() => fichajeEntradaMutation.mutate()}
                disabled={!operarioSeleccionado || operarioSeleccionado === '__none__' || fichajeEntradaMutation.isPending}
              >
                <LogIn className="h-4 w-4 mr-2" />
                Fichar entrada
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: confirmar borrado */}
      <Dialog open={!!fichajeABorrar} onOpenChange={(open) => { if (!open) setFichajeABorrar(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <Trash2 className="h-5 w-5" />
              Eliminar fichaje
            </DialogTitle>
          </DialogHeader>
          {fichajeABorrar && (
            <p className="text-sm text-muted-foreground py-2">
              ¿Eliminar el fichaje de <span className="font-medium text-foreground">{fichajeABorrar.operario_nombre} {fichajeABorrar.operario_apellido}</span> del {formatFechaCorta(fichajeABorrar.fecha)}? Esta acción no se puede deshacer.
            </p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setFichajeABorrar(null)}>Cancelar</Button>
            <Button
              variant="destructive"
              onClick={() => fichajeABorrar && borrarMutation.mutate(fichajeABorrar.id)}
              disabled={borrarMutation.isPending}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: fichar salida por admin */}
      <Dialog open={showSalidaDialog} onOpenChange={(open) => { setShowSalidaDialog(open); if (!open) { setFichajeParaSalida(null); setNotasSalida(''); setHoraSalida(''); setFechaSalida('') } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LogOut className="h-5 w-5" />
              Fichar salida
            </DialogTitle>
          </DialogHeader>
          {fichajeParaSalida && (
            <div className="space-y-4 py-2">
              <div className="bg-muted rounded-lg px-4 py-3 text-sm">
                <p className="font-medium">{fichajeParaSalida.operario_nombre} {fichajeParaSalida.operario_apellido}</p>
                <p className="text-muted-foreground">Entrada: {formatHora(fichajeParaSalida.hora_inicio)}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    Fecha
                  </Label>
                  <Input
                    type="date"
                    value={fechaSalida}
                    min={fechaDeIso(fichajeParaSalida.hora_inicio)}
                    max={fechaHoy()}
                    onChange={(e) => setFechaSalida(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    Hora de salida
                  </Label>
                  <Input
                    type="time"
                    value={horaSalida}
                    onChange={(e) => setHoraSalida(e.target.value)}
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground -mt-2">Pre-cargadas con la fecha de entrada y la hora actual. Modificalas si el cierre fue otro día.</p>
              <div className="space-y-2">
                <Label>Notas de cierre (opcional)</Label>
                <Textarea
                  placeholder="Ej: Cierre manual por admin"
                  value={notasSalida}
                  onChange={(e) => setNotasSalida(e.target.value)}
                  rows={2}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSalidaDialog(false)}>Cancelar</Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={() => fichajeSalidaMutation.mutate()}
              disabled={fichajeSalidaMutation.isPending}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Confirmar salida
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
