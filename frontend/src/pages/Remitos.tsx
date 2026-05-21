import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Download, Search, Loader2, FileText, Eye, Edit, Ban, AlertTriangle, Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
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
import { remitosService, type Remito, type TipoRemito } from '@/services/remitos'
import { useToast } from '@/hooks/use-toast'
import { formatDate } from '@/lib/utils'

export function RemitosPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [tipoFiltro, setTipoFiltro] = useState<'todos' | TipoRemito>('todos')
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [verRemitoId, setVerRemitoId] = useState<string | null>(null)

  // Dialogs de edicion / anulacion / borrado
  const [editandoRemito, setEditandoRemito] = useState<Remito | null>(null)
  const [anulandoRemito, setAnulandoRemito] = useState<Remito | null>(null)
  const [borrandoRemito, setBorrandoRemito] = useState<Remito | null>(null)
  const [motivoAnulacion, setMotivoAnulacion] = useState('')
  const [formEdicion, setFormEdicion] = useState({
    fecha: '',
    destinatario_texto: '',
    responsable_retira: '',
    direccion_entrega: '',
    transportista: '',
    observaciones: '',
  })

  useEffect(() => {
    if (editandoRemito) {
      setFormEdicion({
        fecha: editandoRemito.fecha,
        destinatario_texto: editandoRemito.destinatario_texto || '',
        responsable_retira: editandoRemito.responsable_retira || '',
        direccion_entrega: editandoRemito.direccion_entrega || '',
        transportista: editandoRemito.transportista || '',
        observaciones: editandoRemito.observaciones || '',
      })
    }
  }, [editandoRemito])

  const invalidateRemitos = () => {
    queryClient.invalidateQueries({ queryKey: ['remitos'] })
    queryClient.invalidateQueries({ queryKey: ['remito-detalle'] })
    queryClient.invalidateQueries({ queryKey: ['depositos'] })
    queryClient.invalidateQueries({ queryKey: ['deposito-detail'] })
    queryClient.invalidateQueries({ queryKey: ['materiales'] })
  }

  const editarMutation = useMutation({
    mutationFn: () =>
      remitosService.actualizar(editandoRemito!.id, {
        fecha: formEdicion.fecha || undefined,
        destinatario_texto: formEdicion.destinatario_texto.trim() || null,
        responsable_retira: formEdicion.responsable_retira.trim() || null,
        direccion_entrega: formEdicion.direccion_entrega.trim() || null,
        transportista: formEdicion.transportista.trim() || null,
        observaciones: formEdicion.observaciones.trim() || null,
      }),
    onSuccess: () => {
      invalidateRemitos()
      toast({ title: 'Remito actualizado' })
      setEditandoRemito(null)
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al editar',
        description: e?.response?.data?.detail || '',
      })
    },
  })

  const anularMutation = useMutation({
    mutationFn: () =>
      remitosService.anular(anulandoRemito!.id, motivoAnulacion.trim()),
    onSuccess: () => {
      invalidateRemitos()
      toast({ title: 'Remito anulado, stock revertido' })
      setAnulandoRemito(null)
      setMotivoAnulacion('')
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al anular',
        description: e?.response?.data?.detail || '',
      })
    },
  })

  const borrarMutation = useMutation({
    mutationFn: () => remitosService.borrar(borrandoRemito!.id),
    onSuccess: () => {
      invalidateRemitos()
      toast({ title: 'Remito eliminado del historial' })
      setBorrandoRemito(null)
      // Si el detalle abierto era ese, cerralo
      if (verRemitoId === borrandoRemito?.id) setVerRemitoId(null)
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al eliminar',
        description: e?.response?.data?.detail || '',
      })
    },
  })

  const { data: remitos, isLoading } = useQuery({
    queryKey: ['remitos', { busqueda: search, fechaDesde, fechaHasta, tipo: tipoFiltro }],
    queryFn: () =>
      remitosService.listar({
        busqueda: search || undefined,
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
        tipo: tipoFiltro === 'todos' ? undefined : tipoFiltro,
      }),
  })

  const { data: remitoDetalle, isLoading: loadingDetalle } = useQuery({
    queryKey: ['remito-detalle', verRemitoId],
    queryFn: () => (verRemitoId ? remitosService.obtener(verRemitoId) : null),
    enabled: !!verRemitoId,
  })

  const handleDescargar = async (r: { id: string; numero_formateado: string }) => {
    try {
      setDownloadingId(r.id)
      await remitosService.descargarPdf(r.id, r.numero_formateado)
    } catch {
      toast({ variant: 'destructive', title: 'Error al descargar PDF' })
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Remitos</h1>
          <p className="text-sm text-muted-foreground">
            Historial de salidas de materiales con remito
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-4 space-y-3">
          <div className="flex gap-2">
            {(['todos', 'egreso', 'ingreso'] as const).map((t) => (
              <Button
                key={t}
                size="sm"
                variant={tipoFiltro === t ? 'default' : 'outline'}
                onClick={() => setTipoFiltro(t)}
              >
                {t === 'todos' ? 'Todos' : t === 'egreso' ? 'Egresos' : 'Ingresos'}
              </Button>
            ))}
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por destinatario o responsable..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground whitespace-nowrap">Desde</span>
              <Input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground whitespace-nowrap">Hasta</span>
              <Input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : !remitos || remitos.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <FileText className="h-10 w-10 mx-auto mb-3 opacity-50" />
            No hay remitos generados todavía. Generá uno desde un depósito.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>N°</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Depósito</TableHead>
                <TableHead>Proyecto / Destinatario</TableHead>
                <TableHead className="text-center">Items</TableHead>
                <TableHead>Generado por</TableHead>
                <TableHead className="w-32 text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {remitos.map((r) => (
                <TableRow key={r.id} className={r.anulado ? 'opacity-60' : ''}>
                  <TableCell className="font-mono font-semibold text-sm">
                    <div className="flex flex-col gap-1">
                      <span className={r.anulado ? 'line-through' : ''}>
                        {r.numero_formateado}
                      </span>
                      <div className="flex gap-1 flex-wrap">
                        <Badge
                          variant="outline"
                          className={`text-[10px] px-1 py-0 ${
                            r.tipo === 'ingreso'
                              ? 'border-green-500 text-green-700 bg-green-50'
                              : 'border-blue-500 text-blue-700 bg-blue-50'
                          }`}
                        >
                          {r.tipo === 'ingreso' ? 'INGRESO' : 'EGRESO'}
                        </Badge>
                        {r.anulado && (
                          <Badge variant="destructive" className="text-[10px] px-1 py-0">
                            ANULADO
                          </Badge>
                        )}
                        {r.editado && !r.anulado && (
                          <Badge variant="outline" className="text-[10px] px-1 py-0 border-amber-500 text-amber-700">
                            EDITADO
                          </Badge>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{formatDate(r.fecha)}</TableCell>
                  <TableCell>
                    {r.es_subdeposito && r.deposito_padre_nombre ? (
                      <div className="flex flex-col">
                        <span className="text-xs text-muted-foreground">
                          {r.deposito_padre_nombre}
                        </span>
                        <span className="font-medium text-sm">
                          ↳ {r.deposito_nombre}
                        </span>
                      </div>
                    ) : (
                      r.deposito_nombre || '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {r.proyecto_nombre ? (
                      <Badge variant="outline">{r.proyecto_nombre}</Badge>
                    ) : r.destinatario_texto ? (
                      <span className="text-sm">{r.destinatario_texto}</span>
                    ) : (
                      <span className="text-muted-foreground text-sm">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary">{r.cantidad_items}</Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {r.usuario_nombre || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setVerRemitoId(r.id)}
                        title="Ver detalle"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleDescargar(r)}
                        disabled={downloadingId === r.id}
                        title="Descargar PDF"
                      >
                        {downloadingId === r.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Download className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Dialog detalle */}
      <Dialog open={!!verRemitoId} onOpenChange={(o) => !o && setVerRemitoId(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {remitoDetalle ? `Remito ${remitoDetalle.numero_formateado}` : 'Cargando...'}
            </DialogTitle>
            <DialogDescription>
              {remitoDetalle && formatDate(remitoDetalle.fecha)}
            </DialogDescription>
          </DialogHeader>

          {loadingDetalle || !remitoDetalle ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <DetalleRemito
              remito={remitoDetalle}
              onDescargar={handleDescargar}
              downloading={downloadingId === remitoDetalle.id}
              onEditar={() => setEditandoRemito(remitoDetalle)}
              onAnular={() => setAnulandoRemito(remitoDetalle)}
              onBorrar={() => setBorrandoRemito(remitoDetalle)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog de edicion de datos generales */}
      <Dialog open={!!editandoRemito} onOpenChange={(o) => !o && setEditandoRemito(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Editar remito {editandoRemito?.numero_formateado}
            </DialogTitle>
            <DialogDescription>
              Solo se editan datos generales. Para cambiar materiales o cantidades,
              anulá este remito y creá uno nuevo.
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              editarMutation.mutate()
            }}
            className="space-y-3"
          >
            <div className="space-y-1">
              <Label>Fecha</Label>
              <Input
                type="date"
                value={formEdicion.fecha}
                onChange={(e) => setFormEdicion({ ...formEdicion, fecha: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Destinatario (texto libre)</Label>
              <Input
                value={formEdicion.destinatario_texto}
                onChange={(e) => setFormEdicion({ ...formEdicion, destinatario_texto: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Responsable que retira</Label>
              <Input
                value={formEdicion.responsable_retira}
                onChange={(e) => setFormEdicion({ ...formEdicion, responsable_retira: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Dirección de entrega</Label>
                <Input
                  value={formEdicion.direccion_entrega}
                  onChange={(e) => setFormEdicion({ ...formEdicion, direccion_entrega: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Transportista</Label>
                <Input
                  value={formEdicion.transportista}
                  onChange={(e) => setFormEdicion({ ...formEdicion, transportista: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Observaciones</Label>
              <Textarea
                rows={2}
                value={formEdicion.observaciones}
                onChange={(e) => setFormEdicion({ ...formEdicion, observaciones: e.target.value })}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditandoRemito(null)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={editarMutation.isPending}>
                {editarMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Guardar cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmacion de borrado */}
      <Dialog open={!!borrandoRemito} onOpenChange={(o) => !o && setBorrandoRemito(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Trash2 className="h-5 w-5 text-destructive" />
              Eliminar remito {borrandoRemito?.numero_formateado}
            </DialogTitle>
            <DialogDescription>
              {borrandoRemito?.anulado
                ? 'El remito ya está anulado y se va a eliminar del historial. Esta acción no se puede deshacer.'
                : 'El remito se va a eliminar del historial. Como no estaba anulado, el stock que había descontado se va a devolver primero. Esta acción no se puede deshacer.'}
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button variant="outline" onClick={() => setBorrandoRemito(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => borrarMutation.mutate()}
              disabled={borrarMutation.isPending}
            >
              {borrarMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Eliminar definitivamente
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog de anulacion */}
      <Dialog open={!!anulandoRemito} onOpenChange={(o) => !o && setAnulandoRemito(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Anular remito {anulandoRemito?.numero_formateado}
            </DialogTitle>
            <DialogDescription>
              Esta acción revierte el stock que se había descontado (de todos los
              depósitos donde se haya descontado). El remito queda visible en el
              historial como ANULADO. No se puede deshacer.
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (motivoAnulacion.trim().length < 3) {
                toast({ variant: 'destructive', title: 'El motivo es obligatorio' })
                return
              }
              anularMutation.mutate()
            }}
            className="space-y-3"
          >
            <div className="space-y-1">
              <Label>Motivo de anulación *</Label>
              <Textarea
                rows={3}
                value={motivoAnulacion}
                onChange={(e) => setMotivoAnulacion(e.target.value)}
                placeholder="Ej: Cantidad cargada incorrecta, los materiales no salieron, etc."
                required
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setAnulandoRemito(null)}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={anularMutation.isPending || motivoAnulacion.trim().length < 3}
              >
                {anularMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Anular y revertir stock
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function DetalleRemito({
  remito,
  onDescargar,
  downloading,
  onEditar,
  onAnular,
  onBorrar,
}: {
  remito: Remito
  onDescargar: (r: { id: string; numero_formateado: string }) => void
  downloading: boolean
  onEditar: () => void
  onAnular: () => void
  onBorrar: () => void
}) {
  return (
    <div className="space-y-4">
      {/* Badges de estado */}
      {remito.anulado && (
        <div className="p-3 rounded-md border border-destructive bg-destructive/10 text-sm space-y-1">
          <div className="flex items-center gap-2 text-destructive font-semibold">
            <Ban className="h-4 w-4" />
            Remito ANULADO
          </div>
          {remito.motivo_anulacion && (
            <p className="text-xs"><strong>Motivo:</strong> {remito.motivo_anulacion}</p>
          )}
          {remito.anulado_at && (
            <p className="text-xs text-muted-foreground">
              {formatDate(remito.anulado_at)}
              {remito.anulado_por_nombre ? ` — por ${remito.anulado_por_nombre}` : ''}
            </p>
          )}
        </div>
      )}
      {remito.editado && !remito.anulado && (
        <div className="p-2 rounded-md border border-amber-500 bg-amber-50 text-xs">
          <strong className="text-amber-700">Editado</strong>{' '}
          {remito.editado_at && formatDate(remito.editado_at)}
          {remito.editado_por_nombre ? ` por ${remito.editado_por_nombre}` : ''}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2 text-sm">
        <Field
          label="Depósito"
          value={
            remito.es_subdeposito && remito.deposito_padre_nombre
              ? `${remito.deposito_padre_nombre} → ${remito.deposito_nombre}`
              : remito.deposito_nombre
          }
        />
        <Field label="Proyecto" value={remito.proyecto_nombre} />
        <Field label="Destinatario" value={remito.destinatario_texto} />
        <Field label="Responsable" value={remito.responsable_retira} />
        <Field label="Dirección" value={remito.direccion_entrega} />
        <Field label="Transportista" value={remito.transportista} />
        <Field label="Generado por" value={remito.usuario_nombre} />
      </div>

      {remito.observaciones && (
        <div className="p-3 bg-muted/30 rounded-md text-sm whitespace-pre-wrap">
          {remito.observaciones}
        </div>
      )}

      <div>
        <h4 className="font-medium mb-2">Materiales</h4>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Material</TableHead>
              <TableHead className="text-right">Cantidad</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {remito.items.map((it) => (
              <TableRow key={it.id}>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {it.material_codigo || '-'}
                </TableCell>
                <TableCell>{it.material_nombre}</TableCell>
                <TableCell className="text-right">
                  {Number(it.cantidad).toFixed(2)} {it.material_unidad}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <Button
          variant="outline"
          onClick={onEditar}
          disabled={remito.anulado}
          title={remito.anulado ? 'No se puede editar un remito anulado' : ''}
        >
          <Edit className="h-4 w-4 mr-2" />
          Editar
        </Button>
        <Button
          variant="outline"
          onClick={onAnular}
          disabled={remito.anulado}
          className="text-destructive hover:text-destructive"
          title={remito.anulado ? 'Ya está anulado' : ''}
        >
          <Ban className="h-4 w-4 mr-2" />
          Anular
        </Button>
        <Button onClick={() => onDescargar(remito)} disabled={downloading}>
          {downloading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          PDF
        </Button>
      </div>
      <Button
        variant="ghost"
        onClick={onBorrar}
        className="w-full text-destructive hover:bg-destructive/10 hover:text-destructive"
      >
        <Trash2 className="h-4 w-4 mr-2" />
        Eliminar definitivamente del historial
      </Button>
    </div>
  )
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value || '-'}</p>
    </div>
  )
}
