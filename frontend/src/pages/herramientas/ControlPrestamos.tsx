import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, RotateCcw, History, Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  herramientasService,
  type Herramienta,
  type Prestamo,
  type HerramientaCreate,
  type PrestamoCreate,
  type PrestamoDevolucion,
} from '@/services/herramientas'

export default function ControlPrestamos() {
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogType, setDialogType] = useState<'crear' | 'prestamo' | 'devolucion' | 'historial'>('crear')
  const [selectedHerramienta, setSelectedHerramienta] = useState<Herramienta | null>(null)
  const [historialData, setHistorialData] = useState<Prestamo[]>([])

  // Form states
  const [formNombre, setFormNombre] = useState('')
  const [formDescripcion, setFormDescripcion] = useState('')
  const [formEstado, setFormEstado] = useState<'buen_estado' | 'en_reparacion' | 'rota'>('buen_estado')
  const [formRetiradoPor, setFormRetiradoPor] = useState('')
  const [formFechaRetiro, setFormFechaRetiro] = useState(new Date().toISOString().split('T')[0])
  const [formFechaDevolucion, setFormFechaDevolucion] = useState(new Date().toISOString().split('T')[0])
  const [formNotasDevolucion, setFormNotasDevolucion] = useState('')

  // Queries
  const { data: herramientas, isLoading } = useQuery({
    queryKey: ['herramientas-prestamos'],
    queryFn: () => herramientasService.getHerramientas(),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: HerramientaCreate) => herramientasService.createHerramienta(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['herramientas-prestamos'] })
      closeDialog()
    },
  })

  const prestamoMutation = useMutation({
    mutationFn: (data: PrestamoCreate) => herramientasService.registrarPrestamo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['herramientas-prestamos'] })
      closeDialog()
    },
  })

  const devolucionMutation = useMutation({
    mutationFn: ({ prestamoId, data }: { prestamoId: string; data: PrestamoDevolucion }) =>
      herramientasService.registrarDevolucion(prestamoId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['herramientas-prestamos'] })
      closeDialog()
    },
  })

  const deletePrestamoMutation = useMutation({
    mutationFn: (prestamoId: string) => herramientasService.deletePrestamo(prestamoId),
    onSuccess: () => {
      if (selectedHerramienta) {
        loadHistorial(selectedHerramienta.id)
      }
      queryClient.invalidateQueries({ queryKey: ['herramientas-prestamos'] })
    },
  })

  const closeDialog = () => {
    setDialogOpen(false)
    setSelectedHerramienta(null)
    setFormNombre('')
    setFormDescripcion('')
    setFormEstado('buen_estado')
    setFormRetiradoPor('')
    setFormFechaRetiro(new Date().toISOString().split('T')[0])
    setFormFechaDevolucion(new Date().toISOString().split('T')[0])
    setFormNotasDevolucion('')
    setHistorialData([])
  }

  const openCrearDialog = () => {
    setDialogType('crear')
    setDialogOpen(true)
  }

  const openPrestamoDialog = (herramienta: Herramienta) => {
    setSelectedHerramienta(herramienta)
    setDialogType('prestamo')
    setDialogOpen(true)
  }

  const openDevolucionDialog = async (herramienta: Herramienta) => {
    setSelectedHerramienta(herramienta)
    setDialogType('devolucion')
    setDialogOpen(true)
  }

  const loadHistorial = async (herramientaId: string) => {
    const data = await herramientasService.getHistorialPrestamos(herramientaId)
    setHistorialData(data)
  }

  const openHistorialDialog = async (herramienta: Herramienta) => {
    setSelectedHerramienta(herramienta)
    await loadHistorial(herramienta.id)
    setDialogType('historial')
    setDialogOpen(true)
  }

  const handleCrear = () => {
    createMutation.mutate({
      nombre: formNombre,
      descripcion: formDescripcion || undefined,
      estado: formEstado,
    })
  }

  const handlePrestamo = () => {
    if (!selectedHerramienta) return
    prestamoMutation.mutate({
      herramienta_id: selectedHerramienta.id,
      retirado_por: formRetiradoPor,
      fecha_retiro: formFechaRetiro,
    })
  }

  const handleDevolucion = async () => {
    if (!selectedHerramienta) return
    // Obtener el préstamo activo
    const historial = await herramientasService.getHistorialPrestamos(selectedHerramienta.id, 1)
    const prestamoActivo = historial.find(p => !p.fecha_devolucion)
    if (!prestamoActivo) return

    devolucionMutation.mutate({
      prestamoId: prestamoActivo.id,
      data: {
        fecha_devolucion: formFechaDevolucion,
        notas_devolucion: formNotasDevolucion || undefined,
      },
    })
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('es-AR')
  }

  if (isLoading) {
    return <div className="flex justify-center p-8">Cargando...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-red-600">Control de Préstamos</h1>
        <Button onClick={openCrearDialog} className="bg-red-600 hover:bg-red-700">
          <Plus className="h-4 w-4 mr-2" />
          Añadir Herramienta
        </Button>
      </div>

      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[35%]">Herramienta</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Retirado por</TableHead>
              <TableHead>Fecha de Retiro</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {herramientas?.map(herramienta => (
              <TableRow key={herramienta.id}>
                <TableCell>
                  <div>
                    <p className="font-medium">{herramienta.nombre}</p>
                    {herramienta.descripcion && (
                      <p className="text-sm text-muted-foreground">{herramienta.descripcion}</p>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={herramienta.estado_prestamo === 'disponible' ? 'default' : 'destructive'}
                    className={
                      herramienta.estado_prestamo === 'disponible'
                        ? 'bg-green-500 hover:bg-green-600'
                        : 'bg-red-500'
                    }
                  >
                    {herramienta.estado_prestamo === 'disponible' ? 'Disponible' : 'En Uso'}
                  </Badge>
                </TableCell>
                <TableCell>{herramienta.retirado_por || '-'}</TableCell>
                <TableCell>{formatDate(herramienta.fecha_retiro)}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    {herramienta.estado_prestamo === 'disponible' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openPrestamoDialog(herramienta)}
                        disabled={herramienta.estado === 'rota'}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Registrar Préstamo
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDevolucionDialog(herramienta)}
                      >
                        <RotateCcw className="h-4 w-4 mr-1" />
                        Registrar Devolución
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openHistorialDialog(herramienta)}
                    >
                      <History className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          {dialogType === 'crear' && (
            <>
              <DialogHeader>
                <DialogTitle>Añadir Herramienta</DialogTitle>
                <DialogDescription>
                  Registra una nueva herramienta en el inventario.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="nombre">Nombre *</Label>
                  <Input
                    id="nombre"
                    value={formNombre}
                    onChange={e => setFormNombre(e.target.value)}
                    placeholder="Ej: Amoladora Bosch 900w"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="descripcion">Descripción</Label>
                  <Input
                    id="descripcion"
                    value={formDescripcion}
                    onChange={e => setFormDescripcion(e.target.value)}
                    placeholder="Modelo, características, etc."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="estado">Estado</Label>
                  <Select value={formEstado} onValueChange={(v: typeof formEstado) => setFormEstado(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="buen_estado">Buen Estado</SelectItem>
                      <SelectItem value="en_reparacion">En Reparación</SelectItem>
                      <SelectItem value="rota">Rota</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>
                  Cancelar
                </Button>
                <Button
                  onClick={handleCrear}
                  disabled={!formNombre || createMutation.isPending}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {createMutation.isPending ? 'Guardando...' : 'Guardar'}
                </Button>
              </DialogFooter>
            </>
          )}

          {dialogType === 'prestamo' && selectedHerramienta && (
            <>
              <DialogHeader>
                <DialogTitle>Registrar Préstamo</DialogTitle>
                <DialogDescription>
                  Registrar préstamo de: {selectedHerramienta.nombre}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="retiradoPor">Retirado por *</Label>
                  <Input
                    id="retiradoPor"
                    value={formRetiradoPor}
                    onChange={e => setFormRetiradoPor(e.target.value)}
                    placeholder="Nombre de quien retira"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fechaRetiro">Fecha de retiro *</Label>
                  <Input
                    id="fechaRetiro"
                    type="date"
                    value={formFechaRetiro}
                    onChange={e => setFormFechaRetiro(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>
                  Cancelar
                </Button>
                <Button
                  onClick={handlePrestamo}
                  disabled={!formRetiradoPor || !formFechaRetiro || prestamoMutation.isPending}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {prestamoMutation.isPending ? 'Registrando...' : 'Registrar Préstamo'}
                </Button>
              </DialogFooter>
            </>
          )}

          {dialogType === 'devolucion' && selectedHerramienta && (
            <>
              <DialogHeader>
                <DialogTitle>Registrar Devolución</DialogTitle>
                <DialogDescription>
                  Registrar devolución de: {selectedHerramienta.nombre}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="fechaDevolucion">Fecha de devolución *</Label>
                  <Input
                    id="fechaDevolucion"
                    type="date"
                    value={formFechaDevolucion}
                    onChange={e => setFormFechaDevolucion(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notasDevolucion">Notas de devolución</Label>
                  <Textarea
                    id="notasDevolucion"
                    value={formNotasDevolucion}
                    onChange={e => setFormNotasDevolucion(e.target.value)}
                    placeholder="Observaciones sobre el estado, etc."
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>
                  Cancelar
                </Button>
                <Button
                  onClick={handleDevolucion}
                  disabled={!formFechaDevolucion || devolucionMutation.isPending}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {devolucionMutation.isPending ? 'Registrando...' : 'Registrar Devolución'}
                </Button>
              </DialogFooter>
            </>
          )}

          {dialogType === 'historial' && selectedHerramienta && (
            <>
              <DialogHeader>
                <DialogTitle>Historial de: {selectedHerramienta.nombre}</DialogTitle>
                <DialogDescription>
                  Historial completo de préstamos y devoluciones.
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Retirado por</TableHead>
                      <TableHead>Fecha de Retiro</TableHead>
                      <TableHead>Fecha de Devolución</TableHead>
                      <TableHead>Notas de Devolución</TableHead>
                      <TableHead>Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {historialData.map(prestamo => (
                      <TableRow key={prestamo.id}>
                        <TableCell>{prestamo.retirado_por}</TableCell>
                        <TableCell>{formatDate(prestamo.fecha_retiro)}</TableCell>
                        <TableCell>{formatDate(prestamo.fecha_devolucion)}</TableCell>
                        <TableCell>{prestamo.notas_devolucion || '-'}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-600"
                              onClick={() => deletePrestamoMutation.mutate(prestamo.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {historialData.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground">
                          Sin historial de préstamos
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={closeDialog}>
                  Cerrar
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
