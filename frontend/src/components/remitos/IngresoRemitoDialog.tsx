import { useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Search, Download } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import { proyectosService } from '@/services/proyectos'
import { remitosService } from '@/services/remitos'
import { materialesService } from '@/services/materiales'

interface IngresoRemitoDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  depositoId: string
  depositoNombre?: string
  defaultProyectoId?: string | null
}

interface ItemForm {
  cantidad: string
}

export function IngresoRemitoDialog({
  open,
  onOpenChange,
  depositoId,
  depositoNombre,
  defaultProyectoId,
}: IngresoRemitoDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const today = new Date().toISOString().split('T')[0]
  const [fecha, setFecha] = useState(today)
  const [proyectoId, setProyectoId] = useState<string>('')
  const [proveedor, setProveedor] = useState('')
  const [responsable, setResponsable] = useState('')
  const [direccion, setDireccion] = useState('')
  const [transportista, setTransportista] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [search, setSearch] = useState('')
  const [items, setItems] = useState<Record<string, ItemForm>>({})

  const { data: catalogo, isLoading: loadingCatalogo } = useQuery({
    queryKey: ['materiales-catalogo-min'],
    queryFn: () => materialesService.getMateriales(),
    enabled: open,
  })

  const { data: proyectos } = useQuery({
    queryKey: ['proyectos-todos-min'],
    queryFn: () => proyectosService.getProyectos(),
    enabled: open,
  })

  useEffect(() => {
    if (!open) return
    setFecha(today)
    setProyectoId(defaultProyectoId || '')
    setProveedor('')
    setResponsable('')
    setDireccion('')
    setTransportista('')
    setObservaciones('')
    setSearch('')
    setItems({})
  }, [open, defaultProyectoId])

  const materialesFiltrados = useMemo(() => {
    if (!catalogo) return []
    const q = search.trim().toLowerCase()
    const base = q
      ? catalogo.filter(
          (m) =>
            m.nombre?.toLowerCase().includes(q) ||
            m.codigo?.toLowerCase().includes(q),
        )
      : catalogo
    return [...base].sort((a, b) =>
      (a.nombre ?? '').localeCompare(b.nombre ?? '', 'es', { sensitivity: 'base' }),
    )
  }, [catalogo, search])

  const itemsArmados = useMemo(() => {
    return Object.entries(items)
      .map(([material_id, v]) => ({
        material_id,
        cantidad: parseFloat(v.cantidad) || 0,
      }))
      .filter((it) => it.cantidad > 0)
  }, [items])

  const crearMutation = useMutation({
    mutationFn: () =>
      remitosService.crearIngreso({
        fecha,
        deposito_id: depositoId,
        proyecto_id: proyectoId || undefined,
        destinatario_texto: proveedor.trim() || undefined,
        responsable_retira: responsable.trim() || undefined,
        direccion_entrega: direccion.trim() || undefined,
        transportista: transportista.trim() || undefined,
        observaciones: observaciones.trim() || undefined,
        items: itemsArmados,
      }),
    onSuccess: (remito) => {
      queryClient.invalidateQueries({ queryKey: ['deposito-detail', depositoId] })
      queryClient.invalidateQueries({ queryKey: ['depositos'] })
      queryClient.invalidateQueries({ queryKey: ['materiales'] })
      queryClient.invalidateQueries({ queryKey: ['remitos'] })
      toast({
        title: `Remito de ingreso ${remito.numero_formateado} generado`,
        description: 'Lo podes descargar desde el listado de remitos.',
      })
      onOpenChange(false)
    },
    onError: (e: any) => {
      const detail = e?.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : 'Error al generar remito de ingreso'
      toast({ variant: 'destructive', title: 'Error', description: msg })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (itemsArmados.length === 0) {
      toast({ variant: 'destructive', title: 'Cargá al menos un material con cantidad' })
      return
    }
    crearMutation.mutate()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nuevo ingreso de materiales</DialogTitle>
          <DialogDescription>
            Genera un remito de ingreso a {depositoNombre || 'el depósito'}. El stock se suma al guardar.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Datos generales */}
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Fecha *</Label>
              <Input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label>Proyecto / obra (opcional)</Label>
              <select
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm"
                value={proyectoId}
                onChange={(e) => setProyectoId(e.target.value)}
              >
                <option value="">— Sin proyecto —</option>
                {proyectos?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                    {p.cliente_nombre ? ` · ${p.cliente_nombre}` : ''}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Proveedor / origen</Label>
              <Input
                value={proveedor}
                onChange={(e) => setProveedor(e.target.value)}
                placeholder="Nombre del proveedor u origen del material"
              />
            </div>
            <div className="space-y-1">
              <Label>Responsable que recibe</Label>
              <Input
                value={responsable}
                onChange={(e) => setResponsable(e.target.value)}
                placeholder="Quién recibió el material"
              />
            </div>
            <div className="space-y-1">
              <Label>Dirección de entrega</Label>
              <Input
                value={direccion}
                onChange={(e) => setDireccion(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label>Transportista</Label>
              <Input
                value={transportista}
                onChange={(e) => setTransportista(e.target.value)}
              />
            </div>
          </div>

          {/* Materiales */}
          <div className="space-y-2 pt-2 border-t">
            <div className="flex items-center justify-between">
              <Label className="text-base font-semibold">Materiales que ingresan *</Label>
              <span className="text-xs text-muted-foreground">
                {itemsArmados.length} seleccionado(s)
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Stock mostrado es el global del catálogo. Al guardar, las cantidades se
              suman al depósito de destino.
            </p>

            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar material..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>

            {loadingCatalogo ? (
              <div className="flex justify-center py-6">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : materialesFiltrados.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No hay materiales en el catálogo o no coinciden con la búsqueda.
              </p>
            ) : (
              <div className="border rounded-md max-h-[280px] overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material</TableHead>
                      <TableHead className="text-right">Stock</TableHead>
                      <TableHead className="w-32 text-right">Cantidad ingresada</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {materialesFiltrados.map((m) => {
                      const v = items[m.id]?.cantidad || ''
                      return (
                        <TableRow key={m.id}>
                          <TableCell className="py-2">
                            <div className="font-medium text-sm">{m.nombre}</div>
                            <div className="text-xs text-muted-foreground">
                              {m.codigo} · {m.unidad}
                            </div>
                          </TableCell>
                          <TableCell className="text-right text-sm text-muted-foreground py-2">
                            {Number(m.stock_actual ?? 0).toFixed(2)}
                          </TableCell>
                          <TableCell className="py-2">
                            <Input
                              type="number"
                              min={0}
                              step="any"
                              value={v}
                              onChange={(e) =>
                                setItems((prev) => ({
                                  ...prev,
                                  [m.id]: { cantidad: e.target.value },
                                }))
                              }
                              className="h-8 text-right"
                              placeholder="0"
                            />
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>

          <div className="space-y-1">
            <Label>Observaciones</Label>
            <Textarea
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              placeholder="Notas opcionales (número de factura del proveedor, etc.)"
              rows={2}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={crearMutation.isPending || itemsArmados.length === 0}
              className="bg-green-600 hover:bg-green-700"
            >
              {crearMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Generar remito de ingreso
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
