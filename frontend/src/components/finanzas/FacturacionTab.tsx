import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Loader2, Search, FileText, DollarSign, CheckCircle2, RotateCcw, Eye, Download,
} from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Tabs, TabsList, TabsTrigger, TabsContent,
} from '@/components/ui/tabs'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  listasPrecioService,
  type FacturacionProyectoItem,
  type EstadoFacturacion,
} from '@/services/listasPrecio'
import * as finanzasService from '@/services/finanzas'
import { useToast } from '@/hooks/use-toast'

const METODOS_PAGO: { value: string; label: string }[] = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'tarjeta_debito', label: 'Tarjeta débito' },
  { value: 'tarjeta_credito', label: 'Tarjeta crédito' },
  { value: 'mercado_pago', label: 'Mercado Pago' },
  { value: 'otro', label: 'Otro' },
]

const formatARS = (n: number | null | undefined) =>
  new Intl.NumberFormat('es-AR', {
    style: 'currency', currency: 'ARS', maximumFractionDigits: 2,
  }).format(Number(n || 0))

const formatFecha = (f?: string | null) => {
  if (!f) return '-'
  const [y, m, d] = f.split('-')
  return `${d}/${m}/${y}`
}

const hoyISO = () => new Date().toISOString().split('T')[0]

type FacturarDialogState =
  | { kind: 'facturar'; item: FacturacionProyectoItem }
  | { kind: 'cobrar'; item: FacturacionProyectoItem }
  | { kind: 'detalle'; item: FacturacionProyectoItem }
  | null

export function FacturacionTab() {
  const [tab, setTab] = useState<EstadoFacturacion>('pendiente')
  const [search, setSearch] = useState('')
  const [dialogState, setDialogState] = useState<FacturarDialogState>(null)
  const [numFactura, setNumFactura] = useState('')
  const [fechaFact, setFechaFact] = useState(hoyISO())
  const [montoFact, setMontoFact] = useState<string>('')
  const [fechaCobro, setFechaCobro] = useState(hoyISO())
  const [cuentaCobroId, setCuentaCobroId] = useState<string>('')
  const [metodoPagoCobro, setMetodoPagoCobro] = useState<string>('transferencia')
  const [referenciaCobro, setReferenciaCobro] = useState('')
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: cuentas } = useQuery({
    queryKey: ['cuentas-cobro'],
    queryFn: () => finanzasService.getCuentas(),
  })

  const { data: items, isLoading } = useQuery({
    queryKey: ['facturacion-proyectos', tab],
    queryFn: () => listasPrecioService.getFacturacionProyectos(tab),
  })

  const proyectoDetalleId = dialogState?.kind === 'detalle' ? dialogState.item.proyecto_id : null
  const { data: detalle, isLoading: loadingDetalle } = useQuery({
    queryKey: ['detalle-presupuesto', proyectoDetalleId],
    queryFn: () => listasPrecioService.getDetallePresupuestoProyecto(proyectoDetalleId!),
    enabled: !!proyectoDetalleId,
  })

  const filtrados = useMemo(() => {
    if (!items) return []
    const q = search.trim().toLowerCase()
    if (!q) return items
    return items.filter(
      (t) =>
        t.proyecto_nombre.toLowerCase().includes(q) ||
        t.cliente_nombre?.toLowerCase().includes(q) ||
        t.numero_factura?.toLowerCase().includes(q),
    )
  }, [items, search])

  const totalGrupo = useMemo(
    () =>
      filtrados.reduce((acc, t) => {
        const base = tab === 'pendiente'
          ? Number(t.total_ejecutado || 0)
          : Number(t.monto_facturado ?? t.total_ejecutado ?? 0)
        return acc + base
      }, 0),
    [filtrados, tab],
  )

  const facturarMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: { numero_factura: string; fecha_facturacion: string; monto_facturado?: number | null } }) =>
      listasPrecioService.marcarFacturado(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturacion-proyectos'] })
      toast({ title: 'Proyecto marcado como facturado' })
      cerrarDialog()
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al facturar',
        description: e?.response?.data?.detail,
      })
    },
  })

  const cobrarMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string
      body: {
        fecha_cobro: string
        cuenta_id?: string | null
        metodo_pago?: string | null
        referencia_pago?: string | null
      }
    }) => listasPrecioService.marcarCobrado(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturacion-proyectos'] })
      queryClient.invalidateQueries({ queryKey: ['transacciones'] })
      queryClient.invalidateQueries({ queryKey: ['cuentas'] })
      queryClient.invalidateQueries({ queryKey: ['finanzas-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['resumen-mensual'] })
      queryClient.invalidateQueries({ queryKey: ['cuentas-cobro'] })
      toast({
        title: 'Cobro registrado',
        description: 'Se generó automáticamente un ingreso en la cuenta seleccionada.',
      })
      cerrarDialog()
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al registrar cobro',
        description: e?.response?.data?.detail,
      })
    },
  })

  const revertirMutation = useMutation({
    mutationFn: (id: string) => listasPrecioService.revertirFacturacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturacion-proyectos'] })
      queryClient.invalidateQueries({ queryKey: ['transacciones'] })
      queryClient.invalidateQueries({ queryKey: ['cuentas'] })
      queryClient.invalidateQueries({ queryKey: ['finanzas-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['resumen-mensual'] })
      toast({ title: 'Estado revertido' })
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al revertir',
        description: e?.response?.data?.detail,
      })
    },
  })

  const abrirFacturar = (item: FacturacionProyectoItem) => {
    setNumFactura(item.numero_factura || '')
    setFechaFact(item.fecha_facturacion || hoyISO())
    setMontoFact(
      item.monto_facturado != null
        ? String(item.monto_facturado)
        : String(Number(item.total_ejecutado || 0)),
    )
    setDialogState({ kind: 'facturar', item })
  }

  const abrirCobrar = (item: FacturacionProyectoItem) => {
    setFechaCobro(item.fecha_cobro || hoyISO())
    const cuentaDefault =
      cuentas?.find((c) => c.tipo === 'caja' && c.activo) ||
      cuentas?.find((c) => c.activo)
    setCuentaCobroId(cuentaDefault?.id || '')
    setMetodoPagoCobro('transferencia')
    setReferenciaCobro('')
    setDialogState({ kind: 'cobrar', item })
  }

  const abrirDetalle = (item: FacturacionProyectoItem) => {
    setDialogState({ kind: 'detalle', item })
  }

  const descargarPdf = async (item: FacturacionProyectoItem) => {
    try {
      const blob = await listasPrecioService.descargarPdfFacturacion(item.proyecto_id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const safe = item.proyecto_nombre.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 60)
      a.download = `detalle_${safe}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      toast({ variant: 'destructive', title: 'Error al descargar PDF' })
    }
  }

  const cambiarEstadoDesdeDetalle = async (nuevo: EstadoFacturacion) => {
    if (!dialogState || dialogState.kind !== 'detalle') return
    const item = dialogState.item
    if (nuevo === item.estado_facturacion) return
    if (nuevo === 'facturado') {
      if (item.estado_facturacion === 'cobrado') {
        await revertirMutation.mutateAsync(item.proyecto_id)
        cerrarDialog()
      } else {
        cerrarDialog()
        abrirFacturar(item)
      }
      return
    }
    if (nuevo === 'cobrado') {
      if (item.estado_facturacion === 'pendiente') {
        toast({
          variant: 'destructive',
          title: 'Primero hay que facturar',
          description: 'Marcá facturado antes de registrar el cobro.',
        })
        return
      }
      cerrarDialog()
      abrirCobrar(item)
      return
    }
    if (nuevo === 'pendiente') {
      try {
        if (item.estado_facturacion === 'cobrado') {
          await revertirMutation.mutateAsync(item.proyecto_id)
        }
        await revertirMutation.mutateAsync(item.proyecto_id)
        cerrarDialog()
      } catch {
        // el onError del mutation ya muestra el toast
      }
    }
  }

  const cerrarDialog = () => setDialogState(null)

  const confirmarFacturar = () => {
    if (!dialogState || dialogState.kind !== 'facturar') return
    if (!numFactura.trim() || !fechaFact) {
      toast({ variant: 'destructive', title: 'Faltan datos', description: 'Nº de factura y fecha son obligatorios' })
      return
    }
    facturarMutation.mutate({
      id: dialogState.item.proyecto_id,
      body: {
        numero_factura: numFactura.trim(),
        fecha_facturacion: fechaFact,
        monto_facturado: montoFact ? Number(montoFact) : null,
      },
    })
  }

  const confirmarCobrar = () => {
    if (!dialogState || dialogState.kind !== 'cobrar') return
    if (!fechaCobro) {
      toast({ variant: 'destructive', title: 'Falta la fecha de cobro' })
      return
    }
    cobrarMutation.mutate({
      id: dialogState.item.proyecto_id,
      body: {
        fecha_cobro: fechaCobro,
        cuenta_id: cuentaCobroId || null,
        metodo_pago: metodoPagoCobro || null,
        referencia_pago: referenciaCobro.trim() || null,
      },
    })
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Facturación y cobro</h2>
        <p className="text-sm text-muted-foreground">
          Proyectos finalizados. Marcalos como facturados y registrá el cobro cuando se concrete.
        </p>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as EstadoFacturacion)}>
        <TabsList className="grid w-full grid-cols-3 max-w-2xl">
          <TabsTrigger value="pendiente">Por facturar</TabsTrigger>
          <TabsTrigger value="facturado">Por cobrar</TabsTrigger>
          <TabsTrigger value="cobrado">Cobrados</TabsTrigger>
        </TabsList>

        <Card className="mt-4">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">
              {tab === 'pendiente'
                ? 'Total ejecutado pendiente de facturar'
                : tab === 'facturado'
                ? 'Total facturado pendiente de cobro'
                : 'Total cobrado'}
            </p>
            <p className="text-2xl font-bold text-primary">{formatARS(totalGrupo)}</p>
          </CardContent>
        </Card>

        <div className="relative mt-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar proyecto, cliente o factura..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>

        <TabsContent value="pendiente" className="mt-4">
          {renderTabla('pendiente')}
        </TabsContent>
        <TabsContent value="facturado" className="mt-4">
          {renderTabla('facturado')}
        </TabsContent>
        <TabsContent value="cobrado" className="mt-4">
          {renderTabla('cobrado')}
        </TabsContent>
      </Tabs>

      <Dialog
        open={dialogState?.kind === 'facturar'}
        onOpenChange={(o) => !o && cerrarDialog()}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Marcar como facturado</DialogTitle>
            <DialogDescription>
              {dialogState?.item?.proyecto_nombre}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Nº de factura *</Label>
              <Input
                placeholder="Ej: FAC-A-0001-00001234"
                value={numFactura}
                onChange={(e) => setNumFactura(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Fecha *</Label>
                <Input
                  type="date"
                  value={fechaFact}
                  onChange={(e) => setFechaFact(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Monto facturado</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={montoFact}
                  onChange={(e) => setMontoFact(e.target.value)}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={cerrarDialog}>Cancelar</Button>
            <Button onClick={confirmarFacturar} disabled={facturarMutation.isPending}>
              {facturarMutation.isPending ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Guardando...</>
              ) : 'Confirmar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={dialogState?.kind === 'detalle'}
        onOpenChange={(o) => !o && cerrarDialog()}
      >
        <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Detalle del proyecto</DialogTitle>
            <DialogDescription>
              {dialogState?.kind === 'detalle' && dialogState.item.proyecto_nombre}
              {dialogState?.kind === 'detalle' && dialogState.item.cliente_nombre
                ? ` — ${dialogState.item.cliente_nombre}`
                : ''}
            </DialogDescription>
          </DialogHeader>

          {dialogState?.kind === 'detalle' && (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Estado</Label>
                  <Select
                    value={dialogState.item.estado_facturacion}
                    onValueChange={(v) => cambiarEstadoDesdeDetalle(v as EstadoFacturacion)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pendiente">Pendiente de facturar</SelectItem>
                      <SelectItem value="facturado">Facturado</SelectItem>
                      <SelectItem value="cobrado">Cobrado / Pagado</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Nº de factura</Label>
                  <div className="text-sm font-medium">
                    {dialogState.item.numero_factura || '-'}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Fecha factura / cobro</Label>
                  <div className="text-sm font-medium">
                    {formatFecha(dialogState.item.fecha_facturacion)}
                    {dialogState.item.fecha_cobro ? ` · cobrado el ${formatFecha(dialogState.item.fecha_cobro)}` : ''}
                  </div>
                </div>
              </div>

              {loadingDetalle || !detalle ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : detalle.items.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground text-sm">
                  Este proyecto no tiene actividades cargadas.
                </div>
              ) : (
                <>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Actividad</TableHead>
                          <TableHead className="text-right">Cant. planif.</TableHead>
                          <TableHead className="text-right">Cant. ejec.</TableHead>
                          <TableHead className="text-right">Precio unit.</TableHead>
                          <TableHead className="text-right">Subtotal ejec.</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {detalle.items.map((it) => (
                          <TableRow key={it.proyecto_actividad_id}>
                            <TableCell>
                              <div className="font-medium text-sm">
                                {it.actividad_codigo ? `${it.actividad_codigo} · ` : ''}
                                {it.actividad_nombre}
                              </div>
                              {it.unidad && (
                                <div className="text-xs text-muted-foreground">
                                  Unidad: {it.unidad}
                                </div>
                              )}
                            </TableCell>
                            <TableCell className="text-right font-mono text-sm">
                              {Number(it.cantidad_planificada).toFixed(2)}
                            </TableCell>
                            <TableCell className="text-right font-mono text-sm">
                              {Number(it.cantidad_ejecutada).toFixed(2)}
                            </TableCell>
                            <TableCell className="text-right font-mono text-sm">
                              {formatARS(Number(it.precio_unitario_snapshot))}
                            </TableCell>
                            <TableCell className="text-right font-mono text-sm text-primary">
                              {formatARS(Number(it.subtotal_ejecutado))}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2">
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-xs text-muted-foreground">Total presupuestado</p>
                        <p className="text-xl font-bold">
                          {formatARS(Number(detalle.total_presupuestado))}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-xs text-muted-foreground">Total ejecutado</p>
                        <p className="text-xl font-bold text-primary">
                          {formatARS(Number(detalle.total_ejecutado))}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}
            </div>
          )}

          <DialogFooter className="gap-2">
            {dialogState?.kind === 'detalle' && (
              <Button
                variant="outline"
                onClick={() => descargarPdf(dialogState.item)}
              >
                <Download className="h-4 w-4 mr-2" />
                Descargar PDF
              </Button>
            )}
            <Button variant="outline" onClick={cerrarDialog}>Cerrar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={dialogState?.kind === 'cobrar'}
        onOpenChange={(o) => !o && cerrarDialog()}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar cobro</DialogTitle>
            <DialogDescription>
              {dialogState?.item?.proyecto_nombre}
              {dialogState?.item?.numero_factura ? ` · ${dialogState.item.numero_factura}` : ''}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Fecha de cobro *</Label>
              <Input
                type="date"
                value={fechaCobro}
                onChange={(e) => setFechaCobro(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Cuenta destino *</Label>
              <Select value={cuentaCobroId} onValueChange={setCuentaCobroId}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar cuenta" />
                </SelectTrigger>
                <SelectContent>
                  {(cuentas || [])
                    .filter((c) => c.activo)
                    .map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.nombre} · {c.tipo}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Método de pago</Label>
                <Select value={metodoPagoCobro} onValueChange={setMetodoPagoCobro}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {METODOS_PAGO.map((m) => (
                      <SelectItem key={m.value} value={m.value}>
                        {m.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Referencia</Label>
                <Input
                  placeholder="Nº comprobante / transf."
                  value={referenciaCobro}
                  onChange={(e) => setReferenciaCobro(e.target.value)}
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Se generará automáticamente un ingreso en la cuenta seleccionada por el monto facturado.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={cerrarDialog}>Cancelar</Button>
            <Button onClick={confirmarCobrar} disabled={cobrarMutation.isPending}>
              {cobrarMutation.isPending ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Guardando...</>
              ) : 'Marcar cobrado'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )

  function renderTabla(estado: EstadoFacturacion) {
    if (isLoading) {
      return (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )
    }
    if (filtrados.length === 0) {
      return (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <FileText className="h-10 w-10 mx-auto mb-3 opacity-50" />
            {estado === 'pendiente' && 'No hay proyectos finalizados pendientes de facturar.'}
            {estado === 'facturado' && 'No hay proyectos facturados pendientes de cobro.'}
            {estado === 'cobrado' && 'Todavía no hay proyectos cobrados.'}
          </CardContent>
        </Card>
      )
    }
    return (
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Proyecto</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead>Finalizado</TableHead>
              {estado !== 'pendiente' && <TableHead>Factura</TableHead>}
              {estado !== 'pendiente' && <TableHead>Fecha fact.</TableHead>}
              {estado === 'cobrado' && <TableHead>Fecha cobro</TableHead>}
              <TableHead className="text-right">
                {estado === 'pendiente' ? 'Ejecutado' : 'Monto facturado'}
              </TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtrados.map((t) => {
              const monto = estado === 'pendiente'
                ? Number(t.total_ejecutado || 0)
                : Number(t.monto_facturado ?? t.total_ejecutado ?? 0)
              return (
                <TableRow key={t.proyecto_id}>
                  <TableCell>
                    <div className="font-medium text-sm">{t.proyecto_nombre}</div>
                  </TableCell>
                  <TableCell className="text-sm">{t.cliente_nombre || '-'}</TableCell>
                  <TableCell className="text-sm">{formatFecha(t.fecha_fin_real)}</TableCell>
                  {estado !== 'pendiente' && (
                    <TableCell className="text-sm">
                      {t.numero_factura ? (
                        <Badge variant="outline">{t.numero_factura}</Badge>
                      ) : '-'}
                    </TableCell>
                  )}
                  {estado !== 'pendiente' && (
                    <TableCell className="text-sm">{formatFecha(t.fecha_facturacion)}</TableCell>
                  )}
                  {estado === 'cobrado' && (
                    <TableCell className="text-sm">{formatFecha(t.fecha_cobro)}</TableCell>
                  )}
                  <TableCell className="text-right font-mono text-sm text-primary">
                    {formatARS(monto)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Ver detalle"
                        onClick={() => abrirDetalle(t)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Descargar PDF"
                        onClick={() => descargarPdf(t)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      {estado === 'pendiente' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => abrirFacturar(t)}
                        >
                          <FileText className="h-4 w-4 mr-1" />
                          Facturar
                        </Button>
                      )}
                      {estado === 'facturado' && (
                        <>
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => abrirCobrar(t)}
                          >
                            <DollarSign className="h-4 w-4 mr-1" />
                            Cobrar
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Revertir facturación"
                            onClick={() => revertirMutation.mutate(t.proyecto_id)}
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      {estado === 'cobrado' && (
                        <>
                          <Badge className="bg-green-600 hover:bg-green-600">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Cobrado
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Revertir cobro"
                            onClick={() => revertirMutation.mutate(t.proyecto_id)}
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Card>
    )
  }
}
