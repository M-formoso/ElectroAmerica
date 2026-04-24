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
                Total Actividades
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

      {/* Lista de Actividades */}
      {actividades?.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <CheckCircle2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No hay actividades asignadas a este proyecto
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Las actividades se asignan al crear el proyecto
            </p>
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
                            <Progress value={actividad.porcentaje_avance} className="flex-1 h-2" />
                            <span
                              className={`text-sm font-medium ${getAvanceColor(
                                actividad.porcentaje_avance
                              )}`}
                            >
                              {actividad.porcentaje_avance.toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getAvanceBadge(actividad.porcentaje_avance) as any}>
                        {actividad.porcentaje_avance >= 100
                          ? 'Completada'
                          : actividad.porcentaje_avance > 0
                          ? 'En Progreso'
                          : 'Pendiente'}
                      </Badge>
                      {canEdit && actividad.porcentaje_avance < 100 && (
                        <Button size="sm" onClick={() => openAvanceDialog(actividad)}>
                          <Plus className="h-4 w-4 mr-1" />
                          Registrar Avance
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
                                      {mat.cantidad_total.toFixed(2)} {mat.unidad}
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
                                className="flex items-center justify-between border rounded p-2 text-sm"
                              >
                                <div>
                                  <span className="font-medium">{formatDate(avance.fecha)}</span>
                                  {avance.registrado_por_nombre && (
                                    <span className="text-muted-foreground ml-2">
                                      por {avance.registrado_por_nombre}
                                    </span>
                                  )}
                                  {avance.observaciones && (
                                    <p className="text-muted-foreground text-xs mt-1">
                                      {avance.observaciones}
                                    </p>
                                  )}
                                </div>
                                <Badge variant="outline">
                                  +{avance.cantidad} {actividad.unidad_trabajo}
                                </Badge>
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

      {/* Resumen de Materiales Totales */}
      {resumen?.materiales_totales && resumen.materiales_totales.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Package className="h-4 w-4" />
              Materiales Totales del Proyecto
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Material</TableHead>
                  <TableHead className="text-right">Cantidad Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {resumen.materiales_totales.map((mat) => (
                  <TableRow key={mat.material_id}>
                    <TableCell>{mat.material_nombre}</TableCell>
                    <TableCell className="text-right font-medium">
                      {mat.cantidad_total.toFixed(2)} {mat.unidad}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
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
                  {(selectedActividad.cantidad_planificada - selectedActividad.cantidad_ejecutada).toFixed(
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
                  Máximo: {(selectedActividad.cantidad_planificada - selectedActividad.cantidad_ejecutada).toFixed(2)}
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
    </div>
  )
}
