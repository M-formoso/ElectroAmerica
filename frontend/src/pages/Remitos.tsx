import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Search, Loader2, FileText, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { remitosService, type Remito } from '@/services/remitos'
import { useToast } from '@/hooks/use-toast'
import { formatDate } from '@/lib/utils'

export function RemitosPage() {
  const { toast } = useToast()

  const [search, setSearch] = useState('')
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [verRemitoId, setVerRemitoId] = useState<string | null>(null)

  const { data: remitos, isLoading } = useQuery({
    queryKey: ['remitos', { busqueda: search, fechaDesde, fechaHasta }],
    queryFn: () =>
      remitosService.listar({
        busqueda: search || undefined,
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
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
                <TableRow key={r.id}>
                  <TableCell className="font-mono font-semibold text-sm">
                    {r.numero_formateado}
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
            <DetalleRemito remito={remitoDetalle} onDescargar={handleDescargar} downloading={downloadingId === remitoDetalle.id} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function DetalleRemito({
  remito,
  onDescargar,
  downloading,
}: {
  remito: Remito
  onDescargar: (r: { id: string; numero_formateado: string }) => void
  downloading: boolean
}) {
  return (
    <div className="space-y-4">
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

      <Button
        onClick={() => onDescargar(remito)}
        disabled={downloading}
        className="w-full"
      >
        {downloading ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Download className="h-4 w-4 mr-2" />
        )}
        Descargar PDF
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
