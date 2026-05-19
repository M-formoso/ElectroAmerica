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
import { depositosService } from '@/services/depositos'
import { proyectosService } from '@/services/proyectos'
import { remitosService } from '@/services/remitos'

interface SalidaRemitoDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  depositoId: string
  depositoNombre?: string
  defaultProyectoId?: string | null
}

interface ItemForm {
  cantidad: string
}

export function SalidaRemitoDialog({
  open,
  onOpenChange,
  depositoId,
  depositoNombre,
  defaultProyectoId,
}: SalidaRemitoDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const today = new Date().toISOString().split('T')[0]
  const [fecha, setFecha] = useState(today)
  const [proyectoId, setProyectoId] = useState<string>('')
  const [destinatarioTexto, setDestinatarioTexto] = useState('')
  const [responsable, setResponsable] = useState('')
  const [direccion, setDireccion] = useState('')
  const [transportista, setTransportista] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [search, setSearch] = useState('')
  const [items, setItems] = useState<Record<string, ItemForm>>({})

  const { data: deposito, isLoading: loadingDeposito } = useQuery({
    queryKey: ['deposito-detail', depositoId],
    queryFn: () => depositosService.get(depositoId),
    enabled: open && !!depositoId,
  })

  // Si el deposito de origen es un subdeposito, tambien traemos el detalle
  // del padre para tener la vista consolidada de todo el grupo (padre +
  // hermanos). Asi el usuario puede elegir cualquier material del grupo.
  const padreId = deposito?.parent_id || null
  const { data: padreDeposito, isLoading: loadingPadre } = useQuery({
    queryKey: ['deposito-detail', padreId],
    queryFn: () => depositosService.get(padreId!),
    enabled: open && !!padreId,
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
    setDestinatarioTexto('')
    setResponsable('')
    setDireccion('')
    setTransportista('')
    setObservaciones('')
    setSearch('')
    setItems({})
  }, [open, defaultProyectoId])

  // Fuente de materiales para mostrar en la tabla:
  //  - Si origen es subdeposito: consolidado del padre (todo el grupo).
  //  - Si origen es root: su propio consolidado (incluye sus subdepositos).
  //  - Fallback: materiales directos del origen.
  const materialesFuente = useMemo(() => {
    const fuente = padreDeposito || deposito
    if (!fuente) return [] as Array<{
      material_id: string
      material_codigo?: string
      material_nombre?: string
      material_unidad?: string
      stock_actual: number
    }>
    if (fuente.materiales_totales && fuente.materiales_totales.length > 0) {
      return fuente.materiales_totales.map((m) => ({
        material_id: m.material_id,
        material_codigo: m.material_codigo,
        material_nombre: m.material_nombre,
        material_unidad: m.material_unidad,
        stock_actual: Number(m.stock_total),
      }))
    }
    return fuente.materiales.map((m) => ({
      material_id: m.material_id,
      material_codigo: m.material_codigo,
      material_nombre: m.material_nombre,
      material_unidad: m.material_unidad,
      stock_actual: Number(m.stock_actual),
    }))
  }, [deposito, padreDeposito])

  const materialesFiltrados = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return materialesFuente
    return materialesFuente.filter(
      (m) =>
        m.material_nombre?.toLowerCase().includes(q) ||
        m.material_codigo?.toLowerCase().includes(q),
    )
  }, [materialesFuente, search])

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
      remitosService.crear({
        fecha,
        deposito_id: depositoId,
        proyecto_id: proyectoId || undefined,
        destinatario_texto: destinatarioTexto.trim() || undefined,
        responsable_retira: responsable.trim() || undefined,
        direccion_entrega: direccion.trim() || undefined,
        transportista: transportista.trim() || undefined,
        observaciones: observaciones.trim() || undefined,
        items: itemsArmados,
      }),
    onSuccess: async (remito) => {
      queryClient.invalidateQueries({ queryKey: ['deposito-detail', depositoId] })
      queryClient.invalidateQueries({ queryKey: ['depositos'] })
      queryClient.invalidateQueries({ queryKey: ['materiales'] })
      queryClient.invalidateQueries({ queryKey: ['remitos'] })
      toast({ title: `Remito ${remito.numero_formateado} generado`, description: 'Descargando PDF...' })
      try {
        await remitosService.descargarPdf(remito.id, remito.numero_formateado)
      } catch {
        toast({ variant: 'destructive', title: 'No se pudo descargar el PDF' })
      }
      onOpenChange(false)
    },
    onError: (e: any) => {
      const detail = e?.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : 'Error al generar remito'
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
          <DialogTitle>Nueva salida de materiales</DialogTitle>
          <DialogDescription>
            Genera un remito desde {depositoNombre || 'el depósito'}. El stock se descuenta al guardar.
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
              <Label>Proyecto / obra</Label>
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
              <Label>Destinatario (texto libre)</Label>
              <Input
                value={destinatarioTexto}
                onChange={(e) => setDestinatarioTexto(e.target.value)}
                placeholder="Si no usás un proyecto"
              />
            </div>
            <div className="space-y-1">
              <Label>Responsable que retira</Label>
              <Input
                value={responsable}
                onChange={(e) => setResponsable(e.target.value)}
                placeholder="Nombre del operario / chofer"
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
              <Label className="text-base font-semibold">Materiales a entregar *</Label>
              <span className="text-xs text-muted-foreground">
                {itemsArmados.length} seleccionado(s)
              </span>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar material..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>

            {padreDeposito && (
              <p className="text-xs text-muted-foreground">
                Mostrando el inventario consolidado de <strong>{padreDeposito.nombre}</strong>
                {' '}(todos sus subdepósitos). El descuento prioriza el origen y luego
                los demás del mismo grupo.
              </p>
            )}

            {loadingDeposito || loadingPadre ? (
              <div className="flex justify-center py-6">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : materialesFiltrados.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                {materialesFuente.length === 0
                  ? 'Este depósito no tiene materiales cargados.'
                  : 'No hay materiales que coincidan con la búsqueda.'}
              </p>
            ) : (
              <div className="border rounded-md max-h-[280px] overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material</TableHead>
                      <TableHead className="text-right">Stock</TableHead>
                      <TableHead className="w-32 text-right">Cantidad salida</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {materialesFiltrados.map((m) => {
                      const v = items[m.material_id]?.cantidad || ''
                      const cantidadNum = parseFloat(v) || 0
                      const negativo = cantidadNum > m.stock_actual
                      return (
                        <TableRow key={m.material_id}>
                          <TableCell className="py-2">
                            <div className="font-medium text-sm">{m.material_nombre}</div>
                            <div className="text-xs text-muted-foreground">
                              {m.material_codigo} · {m.material_unidad}
                            </div>
                          </TableCell>
                          <TableCell className="text-right text-sm text-muted-foreground py-2">
                            {m.stock_actual.toFixed(2)}
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
                                  [m.material_id]: { cantidad: e.target.value },
                                }))
                              }
                              className={`h-8 text-right ${negativo ? 'border-amber-500' : ''}`}
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
            {itemsArmados.some((it) => {
              const m = materialesFuente.find((x) => x.material_id === it.material_id)
              return m && it.cantidad > m.stock_actual
            }) && (
              <p className="text-xs text-amber-600">
                Algunos materiales superan el stock del grupo. El faltante se va a marcar
                como salida sin stock en el depósito de origen.
              </p>
            )}
          </div>

          <div className="space-y-1">
            <Label>Observaciones</Label>
            <Textarea
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              placeholder="Notas opcionales..."
              rows={2}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={crearMutation.isPending || itemsArmados.length === 0}>
              {crearMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Generar remito
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
