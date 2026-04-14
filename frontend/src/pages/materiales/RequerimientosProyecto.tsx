import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Package, CheckCircle, Truck, ShoppingCart, AlertTriangle,
  History, MoreHorizontal, ArrowLeft, Calculator, Filter
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui/table'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle
} from '@/components/ui/dialog'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { proyectosService } from '@/services/proyectos'
import { materialesService } from '@/services/materiales'
import {
  requerimientosMaterialService,
  type RequerimientoMaterial,
  type EstadoRequerimiento,
  type PrioridadRequerimiento,
  type OrigenMaterial,
  estadoLabels, estadoColors, prioridadLabels, prioridadColors, origenLabels
} from '@/services/requerimientosMaterial'

export default function RequerimientosProyecto() {
  const { proyectoId } = useParams<{ proyectoId: string }>()
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState('todos')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogType, setDialogType] = useState<'crear' | 'aprobar' | 'estado' | 'entrega' | 'historial'>('crear')
  const [selectedReq, setSelectedReq] = useState<RequerimientoMaterial | null>(null)

  // Form states
  const [formMaterialId, setFormMaterialId] = useState('')
  const [formCantidad, setFormCantidad] = useState('')
  const [formPrioridad, setFormPrioridad] = useState<PrioridadRequerimiento>('media')
  const [formFechaNecesidad, setFormFechaNecesidad] = useState('')
  const [formNotas, setFormNotas] = useState('')
  const [formEstado, setFormEstado] = useState<EstadoRequerimiento>('aprobado')
  const [formOrigen, setFormOrigen] = useState<OrigenMaterial | ''>('')
  const [formCantidadEntrega, setFormCantidadEntrega] = useState('')

  // Queries
  const { data: proyecto } = useQuery({
    queryKey: ['proyecto', proyectoId],
    queryFn: () => proyectosService.getProyecto(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: requerimientos, isLoading } = useQuery({
    queryKey: ['requerimientos', proyectoId],
    queryFn: () => requerimientosMaterialService.getRequerimientos({ proyecto_id: proyectoId }),
    enabled: !!proyectoId,
  })

  const { data: resumen } = useQuery({
    queryKey: ['resumen-materiales', proyectoId],
    queryFn: () => requerimientosMaterialService.getResumenProyecto(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: materiales } = useQuery({
    queryKey: ['materiales-lista'],
    queryFn: () => materialesService.getMateriales(),
  })

  const { data: empresas } = useQuery({
    queryKey: ['empresas-proveedoras'],
    queryFn: () => requerimientosMaterialService.getEmpresas(),
  })

  const [historialData, setHistorialData] = useState<any[]>([])

  // Mutations
  const createMutation = useMutation({
    mutationFn: requerimientosMaterialService.createRequerimiento,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requerimientos', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['resumen-materiales', proyectoId] })
      closeDialog()
    },
  })

  const aprobarMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      requerimientosMaterialService.aprobar(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requerimientos', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['resumen-materiales', proyectoId] })
      closeDialog()
    },
  })

  const cambiarEstadoMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      requerimientosMaterialService.cambiarEstado(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requerimientos', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['resumen-materiales', proyectoId] })
      closeDialog()
    },
  })

  const entregarMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      requerimientosMaterialService.registrarEntrega(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requerimientos', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['resumen-materiales', proyectoId] })
      closeDialog()
    },
  })

  const closeDialog = () => {
    setDialogOpen(false)
    setSelectedReq(null)
    setFormMaterialId('')
    setFormCantidad('')
    setFormPrioridad('media')
    setFormFechaNecesidad('')
    setFormNotas('')
    setFormEstado('aprobado')
    setFormOrigen('')
    setFormCantidadEntrega('')
    setHistorialData([])
  }

  const openCrearDialog = () => {
    setDialogType('crear')
    setDialogOpen(true)
  }

  const openAprobarDialog = (req: RequerimientoMaterial) => {
    setSelectedReq(req)
    setFormCantidad(String(req.cantidad_estimada))
    setDialogType('aprobar')
    setDialogOpen(true)
  }

  const openEstadoDialog = (req: RequerimientoMaterial) => {
    setSelectedReq(req)
    setFormEstado(req.estado)
    setFormOrigen(req.origen || '')
    setDialogType('estado')
    setDialogOpen(true)
  }

  const openEntregaDialog = (req: RequerimientoMaterial) => {
    setSelectedReq(req)
    setFormCantidadEntrega(String(req.cantidad_pendiente))
    setDialogType('entrega')
    setDialogOpen(true)
  }

  const openHistorialDialog = async (req: RequerimientoMaterial) => {
    setSelectedReq(req)
    const historial = await requerimientosMaterialService.getHistorial(req.id)
    setHistorialData(historial)
    setDialogType('historial')
    setDialogOpen(true)
  }

  const handleCrear = () => {
    if (!proyectoId || !formMaterialId || !formCantidad) return
    createMutation.mutate({
      proyecto_id: proyectoId,
      material_id: formMaterialId,
      cantidad_estimada: parseFloat(formCantidad),
      prioridad: formPrioridad,
      fecha_necesidad: formFechaNecesidad || undefined,
      notas: formNotas || undefined,
    })
  }

  const handleAprobar = () => {
    if (!selectedReq || !formCantidad) return
    aprobarMutation.mutate({
      id: selectedReq.id,
      data: {
        cantidad_aprobada: parseFloat(formCantidad),
        notas_aprobacion: formNotas || undefined,
      },
    })
  }

  const handleCambiarEstado = () => {
    if (!selectedReq) return
    cambiarEstadoMutation.mutate({
      id: selectedReq.id,
      data: {
        estado: formEstado,
        origen: formOrigen || undefined,
        motivo: formNotas || undefined,
      },
    })
  }

  const handleEntrega = () => {
    if (!selectedReq || !formCantidadEntrega) return
    entregarMutation.mutate({
      id: selectedReq.id,
      data: {
        cantidad_entregada: parseFloat(formCantidadEntrega),
        notas: formNotas || undefined,
      },
    })
  }

  // Filter requerimientos by tab
  const filteredReqs = requerimientos?.filter(r => {
    if (activeTab === 'todos') return true
    if (activeTab === 'pendientes') return !['entregado_obra', 'consumido', 'cancelado'].includes(r.estado)
    if (activeTab === 'en_obra') return r.estado === 'entregado_obra'
    return true
  })

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('es-AR')
  }

  if (isLoading) {
    return <div className="flex justify-center p-8">Cargando...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to={`/proyectos/${proyectoId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver al proyecto
          </Button>
        </Link>
      </div>

      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Materiales del Proyecto</h1>
          <p className="text-muted-foreground">{proyecto?.nombre}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Calculator className="h-4 w-4 mr-2" />
            Calcular desde Actividad
          </Button>
          <Button onClick={openCrearDialog} className="bg-red-600 hover:bg-red-700">
            <Plus className="h-4 w-4 mr-2" />
            Agregar Material
          </Button>
        </div>
      </div>

      {/* Resumen */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Materiales
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{resumen.total_requerimientos}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Pendientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{resumen.materiales_pendientes}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                En Obra
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{resumen.materiales_en_obra}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Valor Estimado
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {resumen.valor_estimado_total
                  ? `$${resumen.valor_estimado_total.toLocaleString('es-AR')}`
                  : '-'}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabla de requerimientos */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="todos">Todos</TabsTrigger>
          <TabsTrigger value="pendientes">Pendientes</TabsTrigger>
          <TabsTrigger value="en_obra">En Obra</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Material</TableHead>
                  <TableHead>Cantidad</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Prioridad</TableHead>
                  <TableHead>Origen</TableHead>
                  <TableHead>Fecha Necesidad</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReqs?.map(req => (
                  <TableRow key={req.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{req.material_nombre}</p>
                        <p className="text-sm text-muted-foreground">
                          Stock: {req.material_stock} {req.material_unidad}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <p>Est: {req.cantidad_estimada} {req.material_unidad}</p>
                        {req.cantidad_aprobada && (
                          <p className="text-green-600">Apr: {req.cantidad_aprobada}</p>
                        )}
                        {req.cantidad_entregada > 0 && (
                          <p className="text-blue-600">Ent: {req.cantidad_entregada}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={estadoColors[req.estado]}>
                        {estadoLabels[req.estado]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={prioridadColors[req.prioridad]}>
                        {prioridadLabels[req.prioridad]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {req.origen ? origenLabels[req.origen] : '-'}
                      {req.empresa_origen_nombre && (
                        <p className="text-xs text-muted-foreground">{req.empresa_origen_nombre}</p>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(req.fecha_necesidad)}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {req.estado === 'estimado' && (
                            <DropdownMenuItem onClick={() => openAprobarDialog(req)}>
                              <CheckCircle className="h-4 w-4 mr-2" />
                              Aprobar
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem onClick={() => openEstadoDialog(req)}>
                            <ShoppingCart className="h-4 w-4 mr-2" />
                            Cambiar Estado
                          </DropdownMenuItem>
                          {['pendiente_retiro', 'pendiente_entrega'].includes(req.estado) && (
                            <DropdownMenuItem onClick={() => openEntregaDialog(req)}>
                              <Truck className="h-4 w-4 mr-2" />
                              Registrar Entrega
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => openHistorialDialog(req)}>
                            <History className="h-4 w-4 mr-2" />
                            Ver Historial
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
                {filteredReqs?.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                      No hay materiales en esta categoría
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          {dialogType === 'crear' && (
            <>
              <DialogHeader>
                <DialogTitle>Agregar Material</DialogTitle>
                <DialogDescription>
                  Agrega un material manualmente al proyecto
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Material *</Label>
                  <Select value={formMaterialId} onValueChange={setFormMaterialId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar material" />
                    </SelectTrigger>
                    <SelectContent>
                      {materiales?.map(m => (
                        <SelectItem key={m.id} value={m.id}>
                          {m.nombre} ({m.unidad})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Cantidad *</Label>
                  <Input
                    type="number"
                    value={formCantidad}
                    onChange={e => setFormCantidad(e.target.value)}
                    placeholder="Cantidad necesaria"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Prioridad</Label>
                  <Select value={formPrioridad} onValueChange={(v: PrioridadRequerimiento) => setFormPrioridad(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critica">Crítica</SelectItem>
                      <SelectItem value="alta">Alta</SelectItem>
                      <SelectItem value="media">Media</SelectItem>
                      <SelectItem value="baja">Baja</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Fecha de necesidad</Label>
                  <Input
                    type="date"
                    value={formFechaNecesidad}
                    onChange={e => setFormFechaNecesidad(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Notas</Label>
                  <Textarea
                    value={formNotas}
                    onChange={e => setFormNotas(e.target.value)}
                    placeholder="Observaciones adicionales"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>Cancelar</Button>
                <Button
                  onClick={handleCrear}
                  disabled={!formMaterialId || !formCantidad || createMutation.isPending}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {createMutation.isPending ? 'Guardando...' : 'Agregar'}
                </Button>
              </DialogFooter>
            </>
          )}

          {dialogType === 'aprobar' && selectedReq && (
            <>
              <DialogHeader>
                <DialogTitle>Aprobar Requerimiento</DialogTitle>
                <DialogDescription>
                  {selectedReq.material_nombre}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Cantidad a aprobar *</Label>
                  <Input
                    type="number"
                    value={formCantidad}
                    onChange={e => setFormCantidad(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Cantidad estimada: {selectedReq.cantidad_estimada} {selectedReq.material_unidad}
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Notas de aprobación</Label>
                  <Textarea
                    value={formNotas}
                    onChange={e => setFormNotas(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>Cancelar</Button>
                <Button
                  onClick={handleAprobar}
                  disabled={!formCantidad || aprobarMutation.isPending}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {aprobarMutation.isPending ? 'Aprobando...' : 'Aprobar'}
                </Button>
              </DialogFooter>
            </>
          )}

          {dialogType === 'estado' && selectedReq && (
            <>
              <DialogHeader>
                <DialogTitle>Cambiar Estado</DialogTitle>
                <DialogDescription>
                  {selectedReq.material_nombre}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Nuevo estado *</Label>
                  <Select value={formEstado} onValueChange={(v: EstadoRequerimiento) => setFormEstado(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(estadoLabels).map(([value, label]) => (
                        <SelectItem key={value} value={value}>{label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Origen del material</Label>
                  <Select value={formOrigen} onValueChange={(v: OrigenMaterial | '') => setFormOrigen(v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar origen" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="stock_propio">Stock Propio</SelectItem>
                      <SelectItem value="compra">Compra</SelectItem>
                      <SelectItem value="entrega_cliente">Entrega Cliente</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Motivo del cambio</Label>
                  <Textarea
                    value={formNotas}
                    onChange={e => setFormNotas(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>Cancelar</Button>
                <Button
                  onClick={handleCambiarEstado}
                  disabled={cambiarEstadoMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {cambiarEstadoMutation.isPending ? 'Guardando...' : 'Guardar'}
                </Button>
              </DialogFooter>
            </>
          )}

          {dialogType === 'entrega' && selectedReq && (
            <>
              <DialogHeader>
                <DialogTitle>Registrar Entrega</DialogTitle>
                <DialogDescription>
                  {selectedReq.material_nombre}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Cantidad a entregar *</Label>
                  <Input
                    type="number"
                    value={formCantidadEntrega}
                    onChange={e => setFormCantidadEntrega(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Pendiente: {selectedReq.cantidad_pendiente} {selectedReq.material_unidad}
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Notas</Label>
                  <Textarea
                    value={formNotas}
                    onChange={e => setFormNotas(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>Cancelar</Button>
                <Button
                  onClick={handleEntrega}
                  disabled={!formCantidadEntrega || entregarMutation.isPending}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {entregarMutation.isPending ? 'Registrando...' : 'Registrar Entrega'}
                </Button>
              </DialogFooter>
            </>
          )}

          {dialogType === 'historial' && selectedReq && (
            <>
              <DialogHeader>
                <DialogTitle>Historial de Cambios</DialogTitle>
                <DialogDescription>
                  {selectedReq.material_nombre}
                </DialogDescription>
              </DialogHeader>
              <div className="py-4 max-h-96 overflow-y-auto">
                {historialData.length === 0 ? (
                  <p className="text-center text-muted-foreground">Sin historial</p>
                ) : (
                  <div className="space-y-3">
                    {historialData.map((h: any) => (
                      <div key={h.id} className="border rounded p-3 text-sm">
                        <div className="flex justify-between">
                          <span className="font-medium">{h.campo_modificado}</span>
                          <span className="text-muted-foreground">
                            {new Date(h.created_at).toLocaleString('es-AR')}
                          </span>
                        </div>
                        <p>
                          <span className="text-red-500">{h.valor_anterior || '-'}</span>
                          {' → '}
                          <span className="text-green-500">{h.valor_nuevo || '-'}</span>
                        </p>
                        {h.motivo && <p className="text-muted-foreground italic">{h.motivo}</p>}
                        {h.usuario_nombre && <p className="text-xs">Por: {h.usuario_nombre}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>Cerrar</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
