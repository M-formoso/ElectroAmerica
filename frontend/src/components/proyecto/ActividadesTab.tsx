import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  CheckCircle2,
  Clock,
  Play,
  Loader2,
  ChevronDown,
  ChevronUp,
  Package,
  Download,
  Search,
  Check,
  Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  proyectoActividadesService,
  type ProyectoActividadList,
  type AvanceActividad,
  type MaterialCalculado,
} from '@/services/proyectoActividades'
import { actividadesTipoService, type ActividadTipoList } from '@/services/actividadesTipo'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

interface ActividadesTabProps {
  proyectoId: string
  proyectoNombre: string
  canEdit: boolean
}

export function ActividadesTab({ proyectoId, proyectoNombre, canEdit }: ActividadesTabProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  // Estado para descarga
  const [isDownloading, setIsDownloading] = useState(false)

  // Estados para dialog de agregar tareas
  const [isAddTareaDialogOpen, setIsAddTareaDialogOpen] = useState(false)
  const [selectedTareas, setSelectedTareas] = useState<
    Array<{ actividad_tipo_id: string; cantidad_planificada: string }>
  >([])
  const [searchTarea, setSearchTarea] = useState('')

  // Estados para dialogs
  const [isAvanceDialogOpen, setIsAvanceDialogOpen] = useState(false)
  const [selectedActividad, setSelectedActividad] = useState<ProyectoActividadList | null>(null)
  const [avanceForm, setAvanceForm] = useState({
    fecha: new Date().toISOString().split('T')[0],
    cantidad: '',
    observaciones: '',
  })

  // Estado para expandir detalles
  const [expandedActividad, setExpandedActividad] = useState<string | null>(null)

  // Estado para confirmacion de eliminacion
  const [actividadAEliminar, setActividadAEliminar] = useState<ProyectoActividadList | null>(null)

  // Queries
  const { data: actividades, isLoading } = useQuery({
    queryKey: ['proyecto-actividades', proyectoId],
    queryFn: () => proyectoActividadesService.getActividades(proyectoId),
    enabled: !!proyectoId,
  })

  const { data: resumen } = useQuery({
    queryKey: ['proyecto-actividades-resumen', proyectoId],
    queryFn: () => proyectoActividadesService.getResumen(proyectoId),
    enabled: !!proyectoId,
  })

  const { data: actividadDetalle } = useQuery({
    queryKey: ['proyecto-actividad-detalle', proyectoId, expandedActividad],
    queryFn: () =>
      expandedActividad
        ? proyectoActividadesService.getActividad(proyectoId, expandedActividad)
        : null,
    enabled: !!expandedActividad,
  })

  const { data: avances } = useQuery({
    queryKey: ['proyecto-actividad-avances', proyectoId, expandedActividad],
    queryFn: () =>
      expandedActividad
        ? proyectoActividadesService.getAvances(proyectoId, expandedActividad)
        : null,
    enabled: !!expandedActividad,
  })

  // Query para obtener tareas disponibles (actividades tipo)
  const { data: tareasDisponibles } = useQuery({
    queryKey: ['actividades-tipo'],
    queryFn: () => actividadesTipoService.getActividadesTipo(),
    enabled: isAddTareaDialogOpen,
  })

  // Mutation para registrar avance
  const registrarAvanceMutation = useMutation({
    mutationFn: (data: { actividadId: string; fecha: string; cantidad: number; observaciones?: string }) =>
      proyectoActividadesService.createAvance(proyectoId, data.actividadId, {
        fecha: data.fecha,
        cantidad: data.cantidad,
        observaciones: data.observaciones,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades-resumen', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividad-avances', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      toast({ title: 'Avance registrado exitosamente' })
      closeAvanceDialog()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al registrar avance' })
    },
  })

  // Mutation para actualizar cantidad planificada
  const actualizarCantidadMutation = useMutation({
    mutationFn: (data: { actividadId: string; cantidad_planificada: number }) =>
      proyectoActividadesService.updateActividad(proyectoId, data.actividadId, {
        cantidad_planificada: data.cantidad_planificada,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades-resumen', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividad-detalle', proyectoId] })
      toast({ title: 'Cantidad actualizada' })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al actualizar cantidad' })
    },
  })

  // Mutation para eliminar una actividad del proyecto
  const eliminarActividadMutation = useMutation({
    mutationFn: (actividadId: string) =>
      proyectoActividadesService.deleteActividad(proyectoId, actividadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades-resumen', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      toast({ title: 'Tarea eliminada del proyecto' })
      setActividadAEliminar(null)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al eliminar la tarea' })
    },
  })

  // Mutation para agregar tareas al proyecto
  const agregarTareasMutation = useMutation({
    mutationFn: (tareas: Array<{ actividad_tipo_id: string; cantidad_planificada: string }>) =>
      proyectoActividadesService.createActividadesBulk(
        proyectoId,
        tareas.map((t) => ({
          actividad_tipo_id: t.actividad_tipo_id,
          cantidad_planificada: parseFloat(t.cantidad_planificada) || 1,
        }))
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades-resumen', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      toast({ title: 'Tareas agregadas exitosamente' })
      closeAddTareaDialog()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al agregar tareas' })
    },
  })

  const openAddTareaDialog = () => {
    setSelectedTareas([])
    setSearchTarea('')
    setIsAddTareaDialogOpen(true)
  }

  const closeAddTareaDialog = () => {
    setIsAddTareaDialogOpen(false)
    setSelectedTareas([])
    setSearchTarea('')
  }

  const handleAgregarTareas = () => {
    if (selectedTareas.length === 0) return
    agregarTareasMutation.mutate(selectedTareas)
  }

  const toggleTareaSelection = (tareaId: string) => {
    setSelectedTareas((prev) => {
      const yaSeleccionada = prev.some((t) => t.actividad_tipo_id === tareaId)
      return yaSeleccionada
        ? prev.filter((t) => t.actividad_tipo_id !== tareaId)
        : [...prev, { actividad_tipo_id: tareaId, cantidad_planificada: '1' }]
    })
  }

  const setCantidadTarea = (tareaId: string, cantidad: string) => {
    setSelectedTareas((prev) =>
      prev.map((t) =>
        t.actividad_tipo_id === tareaId ? { ...t, cantidad_planificada: cantidad } : t
      )
    )
  }

  // Filtrar tareas ya asignadas y por búsqueda
  const tareasNoAsignadas = tareasDisponibles?.filter((tarea) => {
    const yaAsignada = actividades?.some((a) => a.actividad_tipo_id === tarea.id)
    const coincideBusqueda =
      searchTarea === '' ||
      tarea.nombre.toLowerCase().includes(searchTarea.toLowerCase()) ||
      tarea.codigo.toLowerCase().includes(searchTarea.toLowerCase()) ||
      tarea.categoria.toLowerCase().includes(searchTarea.toLowerCase())
    return !yaAsignada && coincideBusqueda
  })

  const openAvanceDialog = (actividad: ProyectoActividadList) => {
    setSelectedActividad(actividad)
    setAvanceForm({
      fecha: new Date().toISOString().split('T')[0],
      cantidad: '',
      observaciones: '',
    })
    setIsAvanceDialogOpen(true)
  }

  const closeAvanceDialog = () => {
    setIsAvanceDialogOpen(false)
    setSelectedActividad(null)
  }

  const handleRegistrarAvance = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedActividad || !avanceForm.cantidad) return

    registrarAvanceMutation.mutate({
      actividadId: selectedActividad.id,
      fecha: avanceForm.fecha,
      cantidad: parseFloat(avanceForm.cantidad),
      observaciones: avanceForm.observaciones || undefined,
    })
  }

  const handleDescargarPDF = async () => {
    setIsDownloading(true)
    try {
      await proyectoActividadesService.descargarResumenPDF(proyectoId, proyectoNombre)
      toast({ title: 'PDF descargado exitosamente' })
    } catch {
      toast({ variant: 'destructive', title: 'Error al descargar PDF' })
    } finally {
      setIsDownloading(false)
    }
  }

  const getAvanceColor = (porcentaje: number) => {
    if (porcentaje >= 100) return 'text-green-600'
    if (porcentaje >= 50) return 'text-yellow-600'
    return 'text-gray-600'
  }

  const getAvanceBadge = (porcentaje: number) => {
    if (porcentaje >= 100) return 'success'
    if (porcentaje > 0) return 'default'
    return 'secondary'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Resumen */}
      {resumen && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Tareas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{resumen.total_actividades}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                Completadas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {resumen.actividades_completadas}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                <Play className="h-4 w-4 text-blue-600" />
                En Progreso
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {resumen.actividades_en_progreso}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                <Clock className="h-4 w-4 text-gray-600" />
                Pendientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-600">
                {resumen.actividades_pendientes}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Avance Global */}
      {resumen && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Avance Global del Proyecto</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDescargarPDF}
                disabled={isDownloading}
              >
                {isDownloading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Descargar PDF
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Progress value={Number(resumen.porcentaje_avance_global)} className="flex-1" />
              <span className="text-lg font-bold">
                {Number(resumen.porcentaje_avance_global).toFixed(1)}%
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Header de Tareas con botón agregar */}
      {canEdit && (
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Tareas del Proyecto</h3>
          <Button onClick={openAddTareaDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Agregar Tarea
          </Button>
        </div>
      )}

      {/* Lista de Tareas */}
      {actividades?.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <CheckCircle2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No hay tareas asignadas a este proyecto
            </p>
            {canEdit && (
              <Button className="mt-4" onClick={openAddTareaDialog}>
                <Plus className="h-4 w-4 mr-2" />
                Agregar Tarea
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {actividades?.map((actividad) => (
            <Card key={actividad.id}>
              <CardHeader className="py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-1"
                      onClick={() =>
                        setExpandedActividad(
                          expandedActividad === actividad.id ? null : actividad.id
                        )
                      }
                    >
                      {expandedActividad === actividad.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm text-muted-foreground">
                            {actividad.actividad_codigo}
                          </span>
                          <span className="font-medium">{actividad.actividad_nombre}</span>
                          <Badge variant="outline" className="text-xs">
                            {actividad.actividad_categoria}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 mt-1">
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>
                              {actividad.cantidad_ejecutada} / {actividad.cantidad_planificada}{' '}
                              {actividad.unidad_trabajo}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 w-32">
                            <Progress value={Number(actividad.porcentaje_avance)} className="flex-1 h-2" />
                            <span
                              className={`text-sm font-medium ${getAvanceColor(
                                Number(actividad.porcentaje_avance)
                              )}`}
                            >
                              {Number(actividad.porcentaje_avance).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getAvanceBadge(Number(actividad.porcentaje_avance)) as any}>
                        {Number(actividad.porcentaje_avance) >= 100
                          ? 'Completada'
                          : Number(actividad.porcentaje_avance) > 0
                          ? 'En Progreso'
                          : 'Pendiente'}
                      </Badge>
                      {canEdit && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation()
                            setActividadAEliminar(actividad)
                          }}
                          title="Eliminar tarea del proyecto"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>

                {expandedActividad === actividad.id && (
                  <CardContent className="pt-0 border-t">
                    <div className="grid gap-4 md:grid-cols-2 pt-4">
                      {/* Materiales Calculados */}
                      <div>
                        <h4 className="font-medium mb-2 flex items-center gap-2">
                          <Package className="h-4 w-4" />
                          Materiales Necesarios
                        </h4>
                        {actividadDetalle?.materiales_calculados &&
                        actividadDetalle.materiales_calculados.length > 0 ? (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Material</TableHead>
                                <TableHead className="text-right">Cantidad</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {actividadDetalle.materiales_calculados.map(
                                (mat: MaterialCalculado) => (
                                  <TableRow key={mat.material_id}>
                                    <TableCell className="py-2">
                                      {mat.material_nombre}
                                    </TableCell>
                                    <TableCell className="text-right py-2">
                                      {Number(mat.cantidad_total).toFixed(2)} {mat.unidad}
                                    </TableCell>
                                  </TableRow>
                                )
                              )}
                            </TableBody>
                          </Table>
                        ) : (
                          <p className="text-sm text-muted-foreground">
                            Sin materiales asociados
                          </p>
                        )}
                      </div>

                      {/* Historial de Avances */}
                      <div>
                        <h4 className="font-medium mb-2 flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          Historial de Avances
                        </h4>
                        {avances && avances.length > 0 ? (
                          <div className="space-y-2 max-h-48 overflow-y-auto">
                            {avances.map((avance: AvanceActividad) => (
                              <div
                                key={avance.id}
                                className="border rounded p-2 text-sm space-y-1"
                              >
                                <div className="flex items-center justify-between">
                                  <div>
                                    <span className="font-medium">{formatDate(avance.fecha)}</span>
                                    {avance.registrado_por_nombre && (
                                      <span className="text-muted-foreground ml-2">
                                        por {avance.registrado_por_nombre}
                                      </span>
                                    )}
                                  </div>
                                  <Badge variant="outline">
                                    +{avance.cantidad} {actividad.unidad_trabajo}
                                  </Badge>
                                </div>
                                {avance.observaciones && (
                                  <p className="text-muted-foreground text-xs">
                                    {avance.observaciones}
                                  </p>
                                )}
                                {avance.materiales_consumidos && avance.materiales_consumidos.length > 0 && (
                                  <div className="text-xs text-muted-foreground border-t pt-1 mt-1">
                                    <span className="font-medium">Materiales:</span>{' '}
                                    {avance.materiales_consumidos
                                      .map((m) => `${m.material_nombre} ${m.cantidad}${m.unidad}`)
                                      .join(', ')}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">Sin avances registrados</p>
                        )}
                      </div>
                    </div>

                    {/* Editar cantidad planificada */}
                    {canEdit && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="flex items-center gap-4">
                          <Label className="text-sm">Cantidad Planificada:</Label>
                          <Input
                            type="number"
                            className="w-24"
                            defaultValue={actividad.cantidad_planificada}
                            min={1}
                            step={1}
                            onBlur={(e) => {
                              const newVal = parseFloat(e.target.value)
                              if (newVal !== actividad.cantidad_planificada && newVal > 0) {
                                actualizarCantidadMutation.mutate({
                                  actividadId: actividad.id,
                                  cantidad_planificada: newVal,
                                })
                              }
                            }}
                          />
                          <span className="text-sm text-muted-foreground">
                            {actividad.unidad_trabajo}
                          </span>
                        </div>
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
          ))}
        </div>
      )}


      {/* Dialog para registrar avance */}
      <Dialog open={isAvanceDialogOpen} onOpenChange={setIsAvanceDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Registrar Avance</DialogTitle>
            <DialogDescription>
              {selectedActividad && (
                <span>
                  {selectedActividad.actividad_nombre} - Pendiente:{' '}
                  {(Number(selectedActividad.cantidad_planificada) - Number(selectedActividad.cantidad_ejecutada)).toFixed(
                    2
                  )}{' '}
                  {selectedActividad.unidad_trabajo}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleRegistrarAvance} className="space-y-4">
            <div className="space-y-2">
              <Label>Fecha</Label>
              <Input
                type="date"
                value={avanceForm.fecha}
                onChange={(e) => setAvanceForm({ ...avanceForm, fecha: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label>
                Cantidad ({selectedActividad?.unidad_trabajo})
              </Label>
              <Input
                type="number"
                value={avanceForm.cantidad}
                onChange={(e) => setAvanceForm({ ...avanceForm, cantidad: e.target.value })}
                min={0.01}
                step={0.01}
                max={
                  selectedActividad
                    ? selectedActividad.cantidad_planificada - selectedActividad.cantidad_ejecutada
                    : undefined
                }
                required
              />
              {selectedActividad && (
                <p className="text-xs text-muted-foreground">
                  Máximo: {(Number(selectedActividad.cantidad_planificada) - Number(selectedActividad.cantidad_ejecutada)).toFixed(2)}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Observaciones (opcional)</Label>
              <Textarea
                value={avanceForm.observaciones}
                onChange={(e) => setAvanceForm({ ...avanceForm, observaciones: e.target.value })}
                placeholder="Notas sobre el trabajo realizado..."
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeAvanceDialog}>
                Cancelar
              </Button>
              <Button type="submit" disabled={registrarAvanceMutation.isPending}>
                {registrarAvanceMutation.isPending && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Registrar Avance
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog para agregar tareas */}
      <Dialog open={isAddTareaDialogOpen} onOpenChange={setIsAddTareaDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Agregar Tareas al Proyecto</DialogTitle>
            <DialogDescription>
              Selecciona las tareas que deseas agregar a este proyecto
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Buscador */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nombre, código o categoría..."
                value={searchTarea}
                onChange={(e) => setSearchTarea(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Lista de tareas */}
            <div className="max-h-[400px] overflow-y-auto border rounded-md">
              {tareasNoAsignadas && tareasNoAsignadas.length > 0 ? (
                <div className="p-4 space-y-2">
                  {tareasNoAsignadas.map((tarea) => {
                    const seleccionada = selectedTareas.find(
                      (t) => t.actividad_tipo_id === tarea.id
                    )
                    const checked = !!seleccionada
                    return (
                      <div
                        key={tarea.id}
                        className={`w-full border rounded-lg transition-colors ${
                          checked ? 'bg-primary/10 border-primary' : 'hover:bg-muted'
                        }`}
                      >
                        <div
                          role="button"
                          tabIndex={0}
                          className="flex items-center gap-3 p-3 cursor-pointer text-left"
                          onClick={() => toggleTareaSelection(tarea.id)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              toggleTareaSelection(tarea.id)
                            }
                          }}
                        >
                          <span
                            aria-hidden
                            className={`h-4 w-4 shrink-0 rounded-sm border flex items-center justify-center ${
                              checked ? 'bg-primary border-primary' : 'border-primary'
                            }`}
                          >
                            {checked && <Check className="h-3 w-3 text-primary-foreground" />}
                          </span>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-sm text-muted-foreground">
                                {tarea.codigo}
                              </span>
                              <span className="font-medium">{tarea.nombre}</span>
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="outline" className="text-xs">
                                {tarea.categoria}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                Unidad: {tarea.unidad_trabajo}
                              </span>
                              {tarea.cantidad_materiales > 0 && (
                                <span className="text-xs text-muted-foreground">
                                  • {tarea.cantidad_materiales} materiales
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        {checked && (
                          <div
                            className="flex items-center gap-2 px-3 pb-3 pl-10"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Label className="text-xs text-muted-foreground shrink-0">
                              Cantidad planificada:
                            </Label>
                            <Input
                              type="number"
                              min="0"
                              step="0.01"
                              value={seleccionada.cantidad_planificada}
                              onChange={(e) => setCantidadTarea(tarea.id, e.target.value)}
                              className="h-8 w-28"
                              placeholder="1"
                            />
                            <span className="text-xs text-muted-foreground">
                              {tarea.unidad_trabajo}
                            </span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : tareasDisponibles ? (
                <div className="p-8 text-center text-muted-foreground">
                  {searchTarea
                    ? 'No se encontraron tareas con ese criterio'
                    : 'Todas las tareas ya están asignadas al proyecto'}
                </div>
              ) : (
                <div className="p-8 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                </div>
              )}
            </div>

            {/* Contador de selección */}
            {selectedTareas.length > 0 && (
              <p className="text-sm text-muted-foreground">
                {selectedTareas.length} tarea(s) seleccionada(s)
              </p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeAddTareaDialog}>
              Cancelar
            </Button>
            <Button
              onClick={handleAgregarTareas}
              disabled={selectedTareas.length === 0 || agregarTareasMutation.isPending}
            >
              {agregarTareasMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Agregar {selectedTareas.length > 0 ? `(${selectedTareas.length})` : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog confirmacion eliminar actividad */}
      <Dialog
        open={!!actividadAEliminar}
        onOpenChange={(open) => !open && setActividadAEliminar(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar tarea del proyecto</DialogTitle>
            <DialogDescription>
              {actividadAEliminar && (
                <>
                  Vas a eliminar <strong>{actividadAEliminar.actividad_nombre}</strong> del proyecto.
                  {Number(actividadAEliminar.cantidad_ejecutada) > 0 && (
                    <span className="block mt-2 text-destructive">
                      Atencion: esta tarea ya tiene {actividadAEliminar.cantidad_ejecutada} {actividadAEliminar.unidad_trabajo} ejecutados.
                    </span>
                  )}
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setActividadAEliminar(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                actividadAEliminar && eliminarActividadMutation.mutate(actividadAEliminar.id)
              }
              disabled={eliminarActividadMutation.isPending}
            >
              {eliminarActividadMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
