import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Trash2,
  ArrowLeft,
  Building2,
  FileText,
  CheckCircle2,
  Clock,
  Calendar,
  Search,
  Loader2,
  AlertTriangle,
  ClipboardList,
  Edit3,
  RotateCcw,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import { formatCurrency } from '@/lib/utils'
import { facturasService } from '@/services/facturas'
import type {
  EmpresaFacturasResumen,
  Factura,
  FacturaCreate,
  FacturaMesItem,
} from '@/services/facturas'
import { proyectosService } from '@/services/proyectos'
import type { Proyecto } from '@/types'

// Formatea una fecha "YYYY-MM-DD" en formato local sin corrimiento por UTC.
function formatFechaLocal(iso?: string | null): string {
  if (!iso) return '-'
  const [y, m, d] = iso.split('T')[0].split('-').map(Number)
  return `${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}/${y}`
}

function hoyISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

interface FacturaFormState {
  proyecto_id: string
  obra_texto: string
  fecha_inscripcion: string
  monto: string
  descripcion: string
  observaciones: string
}

const emptyFacturaForm: FacturaFormState = {
  proyecto_id: '',
  obra_texto: '',
  fecha_inscripcion: hoyISO(),
  monto: '',
  descripcion: '',
  observaciones: '',
}

const NO_PROYECTO_VALUE = '__sin_proyecto__'

export function FacturasEmpresaTab() {
  const [empresaSeleccionada, setEmpresaSeleccionada] = useState<EmpresaFacturasResumen | null>(null)
  const [busqueda, setBusqueda] = useState('')

  // Dialogs
  const [nuevaEmpresaOpen, setNuevaEmpresaOpen] = useState(false)
  const [confirmarEliminarEmpresa, setConfirmarEliminarEmpresa] = useState<EmpresaFacturasResumen | null>(null)
  const [nuevaFacturaOpen, setNuevaFacturaOpen] = useState(false)
  const [editarFactura, setEditarFactura] = useState<Factura | null>(null)
  const [confirmarEliminarFactura, setConfirmarEliminarFactura] = useState<Factura | null>(null)
  const [pendientesOpen, setPendientesOpen] = useState(false)
  const [pagarFactura, setPagarFactura] = useState<Factura | null>(null)
  const [detalleFactura, setDetalleFactura] = useState<Factura | null>(null)
  const [confirmarMarcarPendiente, setConfirmarMarcarPendiente] = useState<Factura | null>(null)

  // Empresa form
  const [nuevaEmpresaData, setNuevaEmpresaData] = useState({
    razon_social: '',
    nombre_fantasia: '',
    cuit: '',
    email: '',
    telefono: '',
  })

  // Factura form
  const [facturaForm, setFacturaForm] = useState<FacturaFormState>(emptyFacturaForm)

  // Fecha pago para el modal de pagar
  const [fechaPagoInput, setFechaPagoInput] = useState<string>(hoyISO())

  // Tab dentro del detalle de empresa
  const [tabDetalle, setTabDetalle] = useState<'listado' | 'por-mes'>('listado')

  const { toast } = useToast()
  const queryClient = useQueryClient()

  // ==================== QUERIES ====================

  const { data: empresas = [], isLoading: cargandoEmpresas } = useQuery({
    queryKey: ['facturas', 'empresas'],
    queryFn: () => facturasService.listarEmpresas(),
  })

  // Obras de la empresa seleccionada. Sin empresa seleccionada, no cargamos
  // nada (el select vive dentro de los modales que solo se abren con empresa).
  const { data: proyectos = [] } = useQuery({
    queryKey: ['proyectos', 'para-facturas', empresaSeleccionada?.id],
    queryFn: () =>
      proyectosService.getProyectos({
        cliente_id: empresaSeleccionada!.id,
        limit: 100,
      }),
    enabled: !!empresaSeleccionada,
  })

  const { data: facturasEmpresa = [], isLoading: cargandoFacturas } = useQuery({
    queryKey: ['facturas', 'por-cliente', empresaSeleccionada?.id],
    queryFn: () => facturasService.listar({ cliente_id: empresaSeleccionada!.id }),
    enabled: !!empresaSeleccionada,
  })

  const { data: facturasPorMes = [], isLoading: cargandoPorMes } = useQuery({
    queryKey: ['facturas', 'por-mes', empresaSeleccionada?.id],
    queryFn: () => facturasService.porMes({ cliente_id: empresaSeleccionada!.id }),
    enabled: !!empresaSeleccionada && tabDetalle === 'por-mes',
  })

  const { data: pendientes = [], isLoading: cargandoPendientes } = useQuery({
    queryKey: ['facturas', 'pendientes'],
    queryFn: () => facturasService.listarPendientes(),
    enabled: pendientesOpen,
  })

  // ==================== MUTATIONS ====================

  const crearEmpresaMut = useMutation({
    mutationFn: facturasService.crearEmpresa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas', 'empresas'] })
      setNuevaEmpresaOpen(false)
      setNuevaEmpresaData({ razon_social: '', nombre_fantasia: '', cuit: '', email: '', telefono: '' })
      toast({ title: 'Empresa creada', description: 'Ya podes cargar facturas a esta empresa.' })
    },
    onError: (err: any) => {
      toast({
        title: 'Error al crear empresa',
        description: err?.response?.data?.detail || 'Intentalo de nuevo.',
        variant: 'destructive',
      })
    },
  })

  const eliminarEmpresaMut = useMutation({
    mutationFn: (id: string) => facturasService.eliminarEmpresa(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas', 'empresas'] })
      setConfirmarEliminarEmpresa(null)
      toast({ title: 'Empresa eliminada' })
    },
    onError: (err: any) => {
      toast({
        title: 'No se pudo eliminar',
        description: err?.response?.data?.detail || 'La empresa podria tener facturas asociadas.',
        variant: 'destructive',
      })
    },
  })

  const crearFacturaMut = useMutation({
    mutationFn: (payload: FacturaCreate) => facturasService.crear(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
      setNuevaFacturaOpen(false)
      setFacturaForm(emptyFacturaForm)
      toast({ title: 'Factura cargada' })
    },
    onError: (err: any) => {
      toast({
        title: 'Error al cargar factura',
        description: err?.response?.data?.detail || 'Intentalo de nuevo.',
        variant: 'destructive',
      })
    },
  })

  const actualizarFacturaMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      facturasService.actualizar(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
      setEditarFactura(null)
      setFacturaForm(emptyFacturaForm)
      toast({ title: 'Factura actualizada' })
    },
    onError: (err: any) => {
      toast({
        title: 'Error al actualizar',
        description: err?.response?.data?.detail || 'Intentalo de nuevo.',
        variant: 'destructive',
      })
    },
  })

  const eliminarFacturaMut = useMutation({
    mutationFn: (id: string) => facturasService.eliminar(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
      setConfirmarEliminarFactura(null)
      toast({ title: 'Factura eliminada' })
    },
  })

  const marcarPagadaMut = useMutation({
    mutationFn: ({ id, fecha_pago }: { id: string; fecha_pago: string }) =>
      facturasService.marcarPagada(id, { fecha_pago }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
      setPagarFactura(null)
      toast({
        title: 'Factura marcada como pagada',
        description: 'Se registro el ingreso en Finanzas automaticamente.',
      })
    },
    onError: (err: any) => {
      toast({
        title: 'Error al marcar como pagada',
        description: err?.response?.data?.detail || 'Intentalo de nuevo.',
        variant: 'destructive',
      })
    },
  })

  const marcarPendienteMut = useMutation({
    mutationFn: (id: string) => facturasService.marcarPendiente(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
      setConfirmarMarcarPendiente(null)
      toast({ title: 'Factura vuelta a pendiente', description: 'La transaccion asociada fue anulada.' })
    },
  })

  // ==================== DERIVADOS ====================

  const empresasFiltradas = useMemo(() => {
    if (!busqueda.trim()) return empresas
    const q = busqueda.toLowerCase()
    return empresas.filter(
      (e) =>
        e.nombre.toLowerCase().includes(q) ||
        (e.cuit || '').toLowerCase().includes(q) ||
        (e.email || '').toLowerCase().includes(q)
    )
  }, [empresas, busqueda])

  const totalPendienteGlobal = useMemo(
    () => empresas.reduce((acc, e) => acc + e.total_pendiente, 0),
    [empresas]
  )
  const cantPendientesGlobal = useMemo(
    () => empresas.reduce((acc, e) => acc + e.cantidad_pendientes, 0),
    [empresas]
  )

  // ==================== HANDLERS ====================

  function abrirNuevaFactura() {
    setFacturaForm(emptyFacturaForm)
    setNuevaFacturaOpen(true)
  }

  function abrirEditarFactura(f: Factura) {
    setEditarFactura(f)
    setFacturaForm({
      proyecto_id: f.proyecto_id || '',
      obra_texto: f.obra_texto || '',
      fecha_inscripcion: f.fecha_inscripcion,
      monto: String(f.monto),
      descripcion: f.descripcion || '',
      observaciones: f.observaciones || '',
    })
  }

  function submitNuevaFactura(e: React.FormEvent) {
    e.preventDefault()
    if (!empresaSeleccionada) return
    const obraTexto = facturaForm.obra_texto.trim()
    if (!facturaForm.proyecto_id && !obraTexto) {
      toast({
        title: 'Falta la obra',
        description: 'Escribí el nombre de la obra o elegí una del listado.',
        variant: 'destructive',
      })
      return
    }
    const monto = parseFloat(facturaForm.monto)
    if (!monto || monto <= 0) {
      toast({ title: 'Monto invalido', variant: 'destructive' })
      return
    }
    crearFacturaMut.mutate({
      cliente_id: empresaSeleccionada.id,
      proyecto_id: facturaForm.proyecto_id || null,
      obra_texto: obraTexto || null,
      fecha_inscripcion: facturaForm.fecha_inscripcion,
      monto,
      descripcion: facturaForm.descripcion || undefined,
      observaciones: facturaForm.observaciones || undefined,
    })
  }

  function submitEditarFactura(e: React.FormEvent) {
    e.preventDefault()
    if (!editarFactura) return
    const obraTexto = facturaForm.obra_texto.trim()
    if (!facturaForm.proyecto_id && !obraTexto) {
      toast({
        title: 'Falta la obra',
        description: 'Escribí el nombre de la obra o elegí una del listado.',
        variant: 'destructive',
      })
      return
    }
    const monto = parseFloat(facturaForm.monto)
    if (!monto || monto <= 0) {
      toast({ title: 'Monto invalido', variant: 'destructive' })
      return
    }
    actualizarFacturaMut.mutate({
      id: editarFactura.id,
      payload: {
        proyecto_id: facturaForm.proyecto_id || null,
        obra_texto: obraTexto || null,
        fecha_inscripcion: facturaForm.fecha_inscripcion,
        monto,
        descripcion: facturaForm.descripcion || null,
        observaciones: facturaForm.observaciones || null,
      },
    })
  }

  // ==================== RENDER ====================

  if (empresaSeleccionada) {
    return renderDetalleEmpresa()
  }
  return renderListadoEmpresas()

  function renderListadoEmpresas() {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-lg font-semibold">Facturas por empresa</h3>
            <p className="text-sm text-muted-foreground">
              Empresas con múltiples facturas por obra. Marcá el cobro y se registra en Finanzas.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => setPendientesOpen(true)}
              className="border-amber-300 text-amber-700 hover:bg-amber-50"
            >
              <AlertTriangle className="mr-2 h-4 w-4" />
              Ver pendientes ({cantPendientesGlobal})
            </Button>
            <Button onClick={() => setNuevaEmpresaOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Nueva empresa
            </Button>
          </div>
        </div>

        {/* Resumen chips */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground">Empresas</div>
              <div className="text-2xl font-bold mt-1">{empresas.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground">Facturas pendientes</div>
              <div className="text-2xl font-bold mt-1 text-amber-600">{cantPendientesGlobal}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground">Total pendiente</div>
              <div className="text-2xl font-bold mt-1 text-red-600">
                {formatCurrency(totalPendienteGlobal)}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Buscador */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar empresa..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>

        {/* Grid de empresas */}
        {cargandoEmpresas ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : empresasFiltradas.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Building2 className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
              <p className="text-muted-foreground">
                {empresas.length === 0
                  ? 'Todavía no hay empresas cargadas. Empezá creando una.'
                  : 'No se encontraron empresas con esa búsqueda.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {empresasFiltradas.map((empresa) => (
              <Card
                key={empresa.id}
                className="hover:border-primary transition-colors cursor-pointer"
                onClick={() => setEmpresaSeleccionada(empresa)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="h-10 w-10 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Building2 className="h-5 w-5 text-primary" />
                      </div>
                      <div className="min-w-0">
                        <CardTitle className="text-base truncate">{empresa.nombre}</CardTitle>
                        {empresa.cuit && (
                          <p className="text-xs text-muted-foreground mt-0.5">CUIT: {empresa.cuit}</p>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-red-600"
                      onClick={(e) => {
                        e.stopPropagation()
                        setConfirmarEliminarEmpresa(empresa)
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-xs text-muted-foreground">Pendientes</div>
                      <div className="font-semibold text-amber-600">
                        {empresa.cantidad_pendientes}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Total pendiente</div>
                      <div className="font-semibold text-red-600 truncate">
                        {formatCurrency(empresa.total_pendiente)}
                      </div>
                    </div>
                    <div className="col-span-2 pt-2 border-t text-xs text-muted-foreground flex items-center justify-between">
                      <span>{empresa.cantidad_facturas} factura(s) totales</span>
                      <span className="text-emerald-600 font-medium">
                        {formatCurrency(empresa.total_pagado)} cobrado
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {renderDialogs()}
      </div>
    )
  }

  function renderDetalleEmpresa() {
    if (!empresaSeleccionada) return null
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setEmpresaSeleccionada(null)}
              className="mt-1"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h3 className="text-lg font-semibold">{empresaSeleccionada.nombre}</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {empresaSeleccionada.cuit && <span>CUIT: {empresaSeleccionada.cuit} · </span>}
                {empresaSeleccionada.cantidad_facturas} factura(s) ·{' '}
                <span className="text-amber-600 font-medium">
                  {formatCurrency(empresaSeleccionada.total_pendiente)} pendiente
                </span>
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => setPendientesOpen(true)}
              className="border-amber-300 text-amber-700 hover:bg-amber-50"
            >
              <AlertTriangle className="mr-2 h-4 w-4" />
              Pendientes globales
            </Button>
            <Button onClick={abrirNuevaFactura}>
              <Plus className="mr-2 h-4 w-4" />
              Nueva factura
            </Button>
          </div>
        </div>

        <Tabs value={tabDetalle} onValueChange={(v) => setTabDetalle(v as any)}>
          <TabsList>
            <TabsTrigger value="listado">
              <ClipboardList className="h-4 w-4 mr-2" />
              Todas las facturas
            </TabsTrigger>
            <TabsTrigger value="por-mes">
              <Calendar className="h-4 w-4 mr-2" />
              Por mes
            </TabsTrigger>
          </TabsList>

          <TabsContent value="listado" className="mt-4">
            {cargandoFacturas ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : facturasEmpresa.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <FileText className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">
                    No hay facturas cargadas para esta empresa.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Obra</TableHead>
                        <TableHead>Descripción</TableHead>
                        <TableHead>Fecha inscripción</TableHead>
                        <TableHead className="text-right">Monto</TableHead>
                        <TableHead>Fecha pago</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {facturasEmpresa.map((f) => (
                        <TableRow key={f.id}>
                          <TableCell className="font-medium">{f.proyecto_nombre || '-'}</TableCell>
                          <TableCell className="max-w-xs truncate">{f.descripcion || '-'}</TableCell>
                          <TableCell>{formatFechaLocal(f.fecha_inscripcion)}</TableCell>
                          <TableCell className="text-right font-mono">
                            {formatCurrency(f.monto)}
                          </TableCell>
                          <TableCell>{formatFechaLocal(f.fecha_pago)}</TableCell>
                          <TableCell>
                            {f.estado === 'pagada' ? (
                              <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                Pagada
                              </Badge>
                            ) : (
                              <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">
                                <Clock className="h-3 w-3 mr-1" />
                                Pendiente
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              {f.estado === 'pendiente' ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-emerald-700 border-emerald-300 hover:bg-emerald-50"
                                  onClick={() => {
                                    setPagarFactura(f)
                                    setFechaPagoInput(hoyISO())
                                  }}
                                >
                                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                                  Marcar pagada
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => setConfirmarMarcarPendiente(f)}
                                  title="Revertir a pendiente"
                                >
                                  <RotateCcw className="h-3.5 w-3.5" />
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => abrirEditarFactura(f)}
                              >
                                <Edit3 className="h-3.5 w-3.5" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-red-600 hover:text-red-700"
                                onClick={() => setConfirmarEliminarFactura(f)}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="por-mes" className="mt-4">
            {cargandoPorMes ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : facturasPorMes.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Calendar className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">
                    Todavía no hay facturas para agrupar por mes.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {facturasPorMes.map((bucket) => (
                  <BucketMes key={`${bucket.anio}-${bucket.mes}`} bucket={bucket} onVer={setDetalleFactura} />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {renderDialogs()}
      </div>
    )
  }

  function renderDialogs() {
    return (
      <>
        {/* Modal nueva empresa */}
        <Dialog open={nuevaEmpresaOpen} onOpenChange={setNuevaEmpresaOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nueva empresa</DialogTitle>
              <DialogDescription>
                Cargá los datos básicos. Podés completar el resto más adelante desde Clientes.
              </DialogDescription>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (!nuevaEmpresaData.razon_social.trim()) {
                  toast({ title: 'Razón social requerida', variant: 'destructive' })
                  return
                }
                crearEmpresaMut.mutate({
                  razon_social: nuevaEmpresaData.razon_social,
                  nombre_fantasia: nuevaEmpresaData.nombre_fantasia || undefined,
                  cuit: nuevaEmpresaData.cuit || undefined,
                  email: nuevaEmpresaData.email || undefined,
                  telefono: nuevaEmpresaData.telefono || undefined,
                })
              }}
              className="space-y-4"
            >
              <div>
                <Label htmlFor="razon_social">Razón social *</Label>
                <Input
                  id="razon_social"
                  value={nuevaEmpresaData.razon_social}
                  onChange={(e) => setNuevaEmpresaData({ ...nuevaEmpresaData, razon_social: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="nombre_fantasia">Nombre fantasía</Label>
                <Input
                  id="nombre_fantasia"
                  value={nuevaEmpresaData.nombre_fantasia}
                  onChange={(e) => setNuevaEmpresaData({ ...nuevaEmpresaData, nombre_fantasia: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="cuit">CUIT</Label>
                  <Input
                    id="cuit"
                    value={nuevaEmpresaData.cuit}
                    onChange={(e) => setNuevaEmpresaData({ ...nuevaEmpresaData, cuit: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="telefono">Teléfono</Label>
                  <Input
                    id="telefono"
                    value={nuevaEmpresaData.telefono}
                    onChange={(e) => setNuevaEmpresaData({ ...nuevaEmpresaData, telefono: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={nuevaEmpresaData.email}
                  onChange={(e) => setNuevaEmpresaData({ ...nuevaEmpresaData, email: e.target.value })}
                />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setNuevaEmpresaOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={crearEmpresaMut.isPending}>
                  {crearEmpresaMut.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Crear empresa'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Confirmar eliminar empresa */}
        <AlertDialog
          open={!!confirmarEliminarEmpresa}
          onOpenChange={(o) => !o && setConfirmarEliminarEmpresa(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>¿Eliminar empresa?</AlertDialogTitle>
              <AlertDialogDescription>
                Se quitará <b>{confirmarEliminarEmpresa?.nombre}</b> del listado de facturas. Si tiene
                facturas cargadas primero debés eliminarlas.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                onClick={() =>
                  confirmarEliminarEmpresa && eliminarEmpresaMut.mutate(confirmarEliminarEmpresa.id)
                }
                className="bg-red-600 hover:bg-red-700"
              >
                Eliminar
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Modal nueva factura */}
        <Dialog open={nuevaFacturaOpen} onOpenChange={setNuevaFacturaOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nueva factura</DialogTitle>
              <DialogDescription>
                Cargá los datos de la factura para <b>{empresaSeleccionada?.nombre}</b>.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={submitNuevaFactura} className="space-y-4">
              {renderFormFactura(proyectos)}
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setNuevaFacturaOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={crearFacturaMut.isPending}>
                  {crearFacturaMut.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Cargar factura'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal editar factura */}
        <Dialog open={!!editarFactura} onOpenChange={(o) => !o && setEditarFactura(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Editar factura</DialogTitle>
            </DialogHeader>
            <form onSubmit={submitEditarFactura} className="space-y-4">
              {renderFormFactura(proyectos)}
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setEditarFactura(null)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={actualizarFacturaMut.isPending}>
                  {actualizarFacturaMut.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Guardar cambios'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Confirmar eliminar factura */}
        <AlertDialog
          open={!!confirmarEliminarFactura}
          onOpenChange={(o) => !o && setConfirmarEliminarFactura(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>¿Eliminar factura?</AlertDialogTitle>
              <AlertDialogDescription>
                Se eliminará la factura y, si estaba pagada, se anulará la transacción de ingreso
                asociada en Finanzas.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                onClick={() =>
                  confirmarEliminarFactura && eliminarFacturaMut.mutate(confirmarEliminarFactura.id)
                }
                className="bg-red-600 hover:bg-red-700"
              >
                Eliminar
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Confirmar revertir a pendiente */}
        <AlertDialog
          open={!!confirmarMarcarPendiente}
          onOpenChange={(o) => !o && setConfirmarMarcarPendiente(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>¿Volver a pendiente?</AlertDialogTitle>
              <AlertDialogDescription>
                Se anulará la transacción de ingreso asociada en Finanzas y la factura volverá al
                estado pendiente.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                onClick={() =>
                  confirmarMarcarPendiente && marcarPendienteMut.mutate(confirmarMarcarPendiente.id)
                }
              >
                Volver a pendiente
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Modal pagar factura */}
        <Dialog open={!!pagarFactura} onOpenChange={(o) => !o && setPagarFactura(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Marcar como pagada</DialogTitle>
              <DialogDescription>
                Indicá la fecha de pago. Se registrará el ingreso en Finanzas automáticamente.
              </DialogDescription>
            </DialogHeader>
            {pagarFactura && (
              <div className="space-y-4">
                <div className="rounded-md bg-muted p-3 text-sm">
                  <div className="font-medium">
                    {pagarFactura.cliente_nombre} · {pagarFactura.proyecto_nombre}
                  </div>
                  {pagarFactura.descripcion && (
                    <div className="text-muted-foreground mt-1">{pagarFactura.descripcion}</div>
                  )}
                  <div className="mt-2 text-lg font-bold text-primary">
                    {formatCurrency(pagarFactura.monto)}
                  </div>
                </div>
                <div>
                  <Label htmlFor="fecha_pago">Fecha de pago *</Label>
                  <Input
                    id="fecha_pago"
                    type="date"
                    value={fechaPagoInput}
                    onChange={(e) => setFechaPagoInput(e.target.value)}
                  />
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setPagarFactura(null)}>
                Cancelar
              </Button>
              <Button
                onClick={() =>
                  pagarFactura &&
                  marcarPagadaMut.mutate({ id: pagarFactura.id, fecha_pago: fechaPagoInput })
                }
                disabled={marcarPagadaMut.isPending || !fechaPagoInput}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {marcarPagadaMut.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Confirmar pago
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Modal global de pendientes */}
        <Dialog open={pendientesOpen} onOpenChange={setPendientesOpen}>
          <DialogContent className="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                Facturas pendientes de cobro
              </DialogTitle>
              <DialogDescription>
                Detalle de todas las facturas pendientes de todas las empresas. Marcá como pagada
                para que salgan de la lista y se registre el ingreso.
              </DialogDescription>
            </DialogHeader>
            <div className="flex-1 overflow-y-auto -mx-6 px-6">
              {cargandoPendientes ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : pendientes.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle2 className="h-10 w-10 mx-auto text-emerald-500 mb-3" />
                  <p className="text-muted-foreground">
                    No hay facturas pendientes. Todo cobrado.
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Empresa</TableHead>
                      <TableHead>Obra</TableHead>
                      <TableHead>Fecha</TableHead>
                      <TableHead className="text-right">Monto</TableHead>
                      <TableHead className="text-right"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendientes.map((f) => (
                      <TableRow
                        key={f.id}
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => setDetalleFactura(f)}
                      >
                        <TableCell className="font-medium">{f.cliente_nombre}</TableCell>
                        <TableCell>{f.proyecto_nombre}</TableCell>
                        <TableCell>{formatFechaLocal(f.fecha_inscripcion)}</TableCell>
                        <TableCell className="text-right font-mono">
                          {formatCurrency(f.monto)}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-emerald-700 border-emerald-300 hover:bg-emerald-50"
                            onClick={(e) => {
                              e.stopPropagation()
                              setPagarFactura(f)
                              setFechaPagoInput(hoyISO())
                            }}
                          >
                            <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                            Pagar
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
            <DialogFooter className="border-t pt-3">
              <div className="mr-auto text-sm">
                <span className="text-muted-foreground">Total pendiente: </span>
                <span className="font-bold text-red-600">
                  {formatCurrency(pendientes.reduce((a, f) => a + f.monto, 0))}
                </span>
              </div>
              <Button variant="outline" onClick={() => setPendientesOpen(false)}>
                Cerrar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Modal detalle de factura (desde el modal de pendientes o desde por-mes) */}
        <Dialog open={!!detalleFactura} onOpenChange={(o) => !o && setDetalleFactura(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Detalle de factura</DialogTitle>
            </DialogHeader>
            {detalleFactura && (
              <div className="space-y-3 text-sm">
                <DetalleFila label="Empresa" value={detalleFactura.cliente_nombre || '-'} />
                <DetalleFila label="Obra" value={detalleFactura.proyecto_nombre || '-'} />
                <DetalleFila
                  label="Fecha inscripción"
                  value={formatFechaLocal(detalleFactura.fecha_inscripcion)}
                />
                <DetalleFila
                  label="Monto"
                  value={<span className="font-bold text-primary">{formatCurrency(detalleFactura.monto)}</span>}
                />
                <DetalleFila
                  label="Estado"
                  value={
                    detalleFactura.estado === 'pagada' ? (
                      <Badge className="bg-emerald-100 text-emerald-800">
                        Pagada · {formatFechaLocal(detalleFactura.fecha_pago)}
                      </Badge>
                    ) : (
                      <Badge className="bg-amber-100 text-amber-800">Pendiente</Badge>
                    )
                  }
                />
                {detalleFactura.descripcion && (
                  <DetalleFila label="Descripción" value={detalleFactura.descripcion} />
                )}
                {detalleFactura.observaciones && (
                  <DetalleFila label="Observaciones" value={detalleFactura.observaciones} />
                )}
              </div>
            )}
            <DialogFooter>
              {detalleFactura?.estado === 'pendiente' && (
                <Button
                  className="bg-emerald-600 hover:bg-emerald-700"
                  onClick={() => {
                    setPagarFactura(detalleFactura)
                    setFechaPagoInput(hoyISO())
                    setDetalleFactura(null)
                  }}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Marcar pagada
                </Button>
              )}
              <Button variant="outline" onClick={() => setDetalleFactura(null)}>
                Cerrar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </>
    )
  }

  function renderFormFactura(proyectos: Proyecto[]) {
    const hayProyectos = proyectos.length > 0
    const proyectoSelectValue = facturaForm.proyecto_id || NO_PROYECTO_VALUE
    return (
      <>
        <div>
          <Label htmlFor="obra_texto">Obra *</Label>
          <Input
            id="obra_texto"
            placeholder="Ej: Obra Centro, Reforma San Martin, etc."
            value={facturaForm.obra_texto}
            onChange={(e) => setFacturaForm({ ...facturaForm, obra_texto: e.target.value })}
          />
          <p className="text-xs text-muted-foreground mt-1">
            Escribí el nombre de la obra tal cual va a figurar en la factura.
          </p>
        </div>

        {hayProyectos && (
          <div>
            <Label htmlFor="proyecto_vinculo">Vincular a proyecto del sistema (opcional)</Label>
            <Select
              value={proyectoSelectValue}
              onValueChange={(v) => {
                if (v === NO_PROYECTO_VALUE) {
                  setFacturaForm({ ...facturaForm, proyecto_id: '' })
                  return
                }
                const p = proyectos.find((x) => x.id === v)
                setFacturaForm({
                  ...facturaForm,
                  proyecto_id: v,
                  // Autocompletar el nombre si el campo esta vacio
                  obra_texto: facturaForm.obra_texto || (p ? p.nombre : ''),
                })
              }}
            >
              <SelectTrigger id="proyecto_vinculo">
                <SelectValue placeholder="No vincular a ningún proyecto" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NO_PROYECTO_VALUE}>— Sin vincular —</SelectItem>
                {proyectos.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground mt-1">
              Si esta obra ya existe como proyecto en el sistema, vinculala para trazabilidad.
            </p>
          </div>
        )}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="fecha_inscripcion">Fecha inscripción *</Label>
            <Input
              id="fecha_inscripcion"
              type="date"
              value={facturaForm.fecha_inscripcion}
              onChange={(e) => setFacturaForm({ ...facturaForm, fecha_inscripcion: e.target.value })}
              required
            />
          </div>
          <div>
            <Label htmlFor="monto">Monto *</Label>
            <Input
              id="monto"
              type="number"
              step="0.01"
              min="0"
              value={facturaForm.monto}
              onChange={(e) => setFacturaForm({ ...facturaForm, monto: e.target.value })}
              required
            />
          </div>
        </div>
        <div>
          <Label htmlFor="descripcion">Descripción</Label>
          <Textarea
            id="descripcion"
            rows={2}
            value={facturaForm.descripcion}
            onChange={(e) => setFacturaForm({ ...facturaForm, descripcion: e.target.value })}
          />
        </div>
        <div>
          <Label htmlFor="observaciones">Observaciones</Label>
          <Textarea
            id="observaciones"
            rows={2}
            value={facturaForm.observaciones}
            onChange={(e) => setFacturaForm({ ...facturaForm, observaciones: e.target.value })}
          />
        </div>
      </>
    )
  }
}

function DetalleFila({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b pb-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right">{value}</span>
    </div>
  )
}

function BucketMes({
  bucket,
  onVer,
}: {
  bucket: FacturaMesItem
  onVer: (f: Factura) => void
}) {
  const pendientes = bucket.facturas.filter((f) => f.estado === 'pendiente').length
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            {bucket.label}
          </CardTitle>
          <div className="text-sm text-muted-foreground">
            {bucket.cantidad} factura(s) · {pendientes} pendiente(s) ·{' '}
            <span className="font-bold text-primary">{formatCurrency(bucket.total)}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Obra</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead>Fecha pago</TableHead>
              <TableHead className="text-right">Monto</TableHead>
              <TableHead>Estado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {bucket.facturas.map((f) => (
              <TableRow key={f.id} className="cursor-pointer hover:bg-accent" onClick={() => onVer(f)}>
                <TableCell className="font-medium">{f.proyecto_nombre}</TableCell>
                <TableCell className="max-w-xs truncate">{f.descripcion || '-'}</TableCell>
                <TableCell>
                  {f.fecha_pago ? formatFechaLocal(f.fecha_pago) : (
                    <span className="text-muted-foreground italic">sin pago</span>
                  )}
                </TableCell>
                <TableCell className="text-right font-mono">{formatCurrency(f.monto)}</TableCell>
                <TableCell>
                  {f.estado === 'pagada' ? (
                    <Badge className="bg-emerald-100 text-emerald-800">Pagada</Badge>
                  ) : (
                    <Badge className="bg-amber-100 text-amber-800">Pendiente</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
