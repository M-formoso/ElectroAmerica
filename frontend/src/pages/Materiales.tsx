import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Search,
  Package,
  AlertTriangle,
  ArrowUpCircle,
  ArrowDownCircle,
  ArrowRightLeft,
  MoreVertical,
  Edit,
  Trash2,
  Loader2,
  History,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  MapPin,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ViewToggle, type ViewMode } from '@/components/ui/view-toggle'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Label } from '@/components/ui/label'
import { materialesService, type MovimientoStock } from '@/services/materiales'
import { DepositoSelector } from '@/components/materiales/DepositoSelector'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import type { Material } from '@/types'

interface MaterialForm {
  codigo: string
  nombre: string
  descripcion: string
  unidad: string
  stock_actual: string
  stock_minimo: string
  precio_unitario: string
  ubicacion_almacen: string
}

const initialFormState: MaterialForm = {
  codigo: '',
  nombre: '',
  descripcion: '',
  unidad: 'unidad',
  stock_actual: '0',
  stock_minimo: '0',
  precio_unitario: '',
  ubicacion_almacen: '',
}

interface DestinoForm {
  deposito_id: string
  cantidad: string
}

export function MaterialesPage() {
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isMovimientoOpen, setIsMovimientoOpen] = useState(false)
  const [isHistorialOpen, setIsHistorialOpen] = useState(false)
  const [isTransferirOpen, setIsTransferirOpen] = useState(false)
  const [movimientoTipo, setMovimientoTipo] = useState<'entrada' | 'salida'>('entrada')
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null)
  const [movimientoCantidad, setMovimientoCantidad] = useState('')
  const [movimientoMotivo, setMovimientoMotivo] = useState('')
  const [transferirCantidad, setTransferirCantidad] = useState('')
  const [transferirMotivo, setTransferirMotivo] = useState('')
  const [transferirDepositoId, setTransferirDepositoId] = useState('')
  const [formData, setFormData] = useState<MaterialForm>(initialFormState)
  const [destinosIniciales, setDestinosIniciales] = useState<DestinoForm[]>([])

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  const { data: materiales, isLoading } = useQuery({
    queryKey: ['materiales'],
    queryFn: () => materialesService.getMateriales(),
  })

  const { data: stockBajo } = useQuery({
    queryKey: ['materiales-stock-bajo'],
    queryFn: materialesService.getStockBajo,
  })

  const { data: movimientos, isLoading: isLoadingMovimientos } = useQuery({
    queryKey: ['movimientos', selectedMaterial?.id],
    queryFn: () => materialesService.getMovimientos(selectedMaterial!.id),
    enabled: !!selectedMaterial && isHistorialOpen,
  })

  const entradaMutation = useMutation({
    mutationFn: ({ id, cantidad, motivo }: { id: string; cantidad: number; motivo: string }) =>
      materialesService.registrarEntrada(id, cantidad, motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materiales'] })
      queryClient.invalidateQueries({ queryKey: ['materiales-stock-bajo'] })
      toast({ title: 'Entrada registrada correctamente' })
      setIsMovimientoOpen(false)
      resetMovimientoForm()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al registrar entrada' })
    },
  })

  const salidaMutation = useMutation({
    mutationFn: ({ id, cantidad, motivo }: { id: string; cantidad: number; motivo: string }) =>
      materialesService.registrarSalida(id, cantidad, motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materiales'] })
      queryClient.invalidateQueries({ queryKey: ['materiales-stock-bajo'] })
      toast({ title: 'Salida registrada correctamente' })
      setIsMovimientoOpen(false)
      resetMovimientoForm()
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al registrar salida',
        description: error.response?.data?.detail || 'Stock insuficiente',
      })
    },
  })

  const createMutation = useMutation({
    mutationFn: materialesService.createMaterial,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materiales'] })
      toast({ title: 'Material creado exitosamente' })
      setIsCreateOpen(false)
      setFormData(initialFormState)
      setDestinosIniciales([])
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al crear material' })
    },
  })

  const transferirMutation = useMutation({
    mutationFn: ({
      materialId,
      payload,
    }: {
      materialId: string
      payload: { deposito_id: string; cantidad: number; motivo?: string }
    }) => materialesService.transferirADeposito(materialId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materiales'] })
      queryClient.invalidateQueries({ queryKey: ['materiales-stock-bajo'] })
      queryClient.invalidateQueries({ queryKey: ['depositos'] })
      toast({ title: 'Stock transferido al depósito' })
      setIsTransferirOpen(false)
      setTransferirCantidad('')
      setTransferirMotivo('')
      setTransferirDepositoId('')
      setSelectedMaterial(null)
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al transferir',
        description: error.response?.data?.detail || 'Verificá el stock disponible',
      })
    },
  })

  const resetMovimientoForm = () => {
    setMovimientoCantidad('')
    setMovimientoMotivo('')
    setSelectedMaterial(null)
  }

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const destinos = destinosIniciales
      .filter((d) => d.deposito_id && parseFloat(d.cantidad) > 0)
      .map((d) => ({ deposito_id: d.deposito_id, cantidad: parseFloat(d.cantidad) }))
    createMutation.mutate({
      codigo: formData.codigo,
      nombre: formData.nombre,
      descripcion: formData.descripcion || undefined,
      unidad: formData.unidad,
      stock_actual: parseFloat(formData.stock_actual) || 0,
      stock_minimo: parseFloat(formData.stock_minimo) || 0,
      precio_unitario: formData.precio_unitario ? parseFloat(formData.precio_unitario) : undefined,
      ubicacion_almacen: formData.ubicacion_almacen || undefined,
      destinos_iniciales: destinos.length > 0 ? destinos : undefined,
    })
  }

  const handleTransferir = () => {
    if (!selectedMaterial || !transferirDepositoId || !transferirCantidad) return
    transferirMutation.mutate({
      materialId: selectedMaterial.id,
      payload: {
        deposito_id: transferirDepositoId,
        cantidad: parseFloat(transferirCantidad),
        motivo: transferirMotivo || undefined,
      },
    })
  }

  const handleMovimiento = () => {
    if (!selectedMaterial || !movimientoCantidad) return

    const data = {
      id: selectedMaterial.id,
      cantidad: parseFloat(movimientoCantidad),
      motivo: movimientoMotivo,
    }

    if (movimientoTipo === 'entrada') {
      entradaMutation.mutate(data)
    } else {
      salidaMutation.mutate(data)
    }
  }

  const filteredMateriales = materiales?.filter((m) =>
    m.nombre.toLowerCase().includes(search.toLowerCase()) ||
    m.codigo.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Materiales</h1>
          <p className="text-muted-foreground">
            Gestiona el inventario de materiales
          </p>
        </div>
        {isAdmin && (
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Material
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Materiales</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{materiales?.length || 0}</div>
          </CardContent>
        </Card>

        <Card className={stockBajo && stockBajo.length > 0 ? 'border-yellow-500' : ''}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Stock Bajo</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {stockBajo?.length || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              materiales por debajo del mínimo
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Valor Total</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(
                materiales?.reduce(
                  (acc, m) => acc + (m.stock_actual * (m.precio_unitario || 0)),
                  0
                ) || 0
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and View Toggle */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre o código..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <ViewToggle viewMode={viewMode} onViewModeChange={setViewMode} />
      </div>

      {/* Cards View */}
      {viewMode === 'cards' && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
            [...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader className="space-y-2">
                  <div className="h-5 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 bg-muted rounded w-1/4" />
                </CardContent>
              </Card>
            ))
          ) : filteredMateriales?.length === 0 ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              No se encontraron materiales
            </div>
          ) : (
            filteredMateriales?.map((material) => (
              <Card key={material.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1 min-w-0">
                      <CardTitle className="text-lg truncate flex items-center gap-2">
                        <Package className="h-4 w-4 text-muted-foreground" />
                        {material.nombre}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground font-mono">
                        {material.codigo}
                      </p>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setMovimientoTipo('entrada')
                            setIsMovimientoOpen(true)
                          }}
                        >
                          <ArrowUpCircle className="h-4 w-4 mr-2 text-green-600" />
                          Entrada
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setMovimientoTipo('salida')
                            setIsMovimientoOpen(true)
                          }}
                        >
                          <ArrowDownCircle className="h-4 w-4 mr-2 text-red-600" />
                          Salida
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setIsTransferirOpen(true)
                          }}
                        >
                          <ArrowRightLeft className="h-4 w-4 mr-2 text-blue-600" />
                          Transferir a depósito
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setIsHistorialOpen(true)
                          }}
                        >
                          <History className="h-4 w-4 mr-2" />
                          Historial
                        </DropdownMenuItem>
                        {isAdmin && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>
                              <Edit className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-destructive">
                              <Trash2 className="h-4 w-4 mr-2" />
                              Eliminar
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Stock</span>
                    <span className="font-bold">
                      {material.stock_actual} {material.unidad}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Minimo</span>
                    <span className="text-sm">
                      {material.stock_minimo} {material.unidad}
                    </span>
                  </div>
                  {material.precio_unitario && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Precio</span>
                      <span className="text-sm font-medium">
                        {formatCurrency(material.precio_unitario)}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-2 border-t">
                    {material.stock_actual <= material.stock_minimo ? (
                      <Badge variant="warning">Stock bajo</Badge>
                    ) : (
                      <Badge variant="success">OK</Badge>
                    )}
                    {material.ubicacion_almacen && (
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {material.ubicacion_almacen}
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Table View */}
      {viewMode === 'list' && (
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Nombre</TableHead>
              <TableHead>Stock</TableHead>
              <TableHead>Mínimo</TableHead>
              <TableHead>Precio Unit.</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-[100px]">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <TableRow key={i}>
                  {[...Array(7)].map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 bg-muted rounded animate-pulse" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : filteredMateriales?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  No se encontraron materiales
                </TableCell>
              </TableRow>
            ) : (
              filteredMateriales?.map((material) => (
                <TableRow key={material.id}>
                  <TableCell className="font-mono text-sm">
                    {material.codigo}
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{material.nombre}</p>
                      {material.ubicacion_almacen && (
                        <p className="text-xs text-muted-foreground">
                          {material.ubicacion_almacen}
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {material.stock_actual} {material.unidad}
                  </TableCell>
                  <TableCell>
                    {material.stock_minimo} {material.unidad}
                  </TableCell>
                  <TableCell>
                    {material.precio_unitario
                      ? formatCurrency(material.precio_unitario)
                      : '-'}
                  </TableCell>
                  <TableCell>
                    {material.stock_actual <= material.stock_minimo ? (
                      <Badge variant="warning">Stock bajo</Badge>
                    ) : (
                      <Badge variant="success">OK</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setMovimientoTipo('entrada')
                            setIsMovimientoOpen(true)
                          }}
                        >
                          <ArrowUpCircle className="h-4 w-4 mr-2 text-green-600" />
                          Entrada
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setMovimientoTipo('salida')
                            setIsMovimientoOpen(true)
                          }}
                        >
                          <ArrowDownCircle className="h-4 w-4 mr-2 text-red-600" />
                          Salida
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setIsTransferirOpen(true)
                          }}
                        >
                          <ArrowRightLeft className="h-4 w-4 mr-2 text-blue-600" />
                          Transferir a depósito
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMaterial(material)
                            setIsHistorialOpen(true)
                          }}
                        >
                          <History className="h-4 w-4 mr-2" />
                          Historial
                        </DropdownMenuItem>
                        {isAdmin && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>
                              <Edit className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-destructive">
                              <Trash2 className="h-4 w-4 mr-2" />
                              Eliminar
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
      )}

      {/* Create material dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Nuevo Material</DialogTitle>
            <DialogDescription>
              Ingresa los datos del nuevo material
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="codigo">Código *</Label>
                  <Input
                    id="codigo"
                    value={formData.codigo}
                    onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
                    placeholder="MAT-001"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="unidad">Unidad *</Label>
                  <Input
                    id="unidad"
                    value={formData.unidad}
                    onChange={(e) => setFormData({ ...formData, unidad: e.target.value })}
                    placeholder="kg, m, unidad..."
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre *</Label>
                <Input
                  id="nombre"
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  placeholder="Nombre del material"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="descripcion">Descripción</Label>
                <Input
                  id="descripcion"
                  value={formData.descripcion}
                  onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                  placeholder="Descripción opcional"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="stock_actual">Stock Inicial</Label>
                  <Input
                    id="stock_actual"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.stock_actual}
                    onChange={(e) => setFormData({ ...formData, stock_actual: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="stock_minimo">Stock Mínimo</Label>
                  <Input
                    id="stock_minimo"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.stock_minimo}
                    onChange={(e) => setFormData({ ...formData, stock_minimo: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="precio_unitario">Precio Unit.</Label>
                  <Input
                    id="precio_unitario"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.precio_unitario}
                    onChange={(e) => setFormData({ ...formData, precio_unitario: e.target.value })}
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="ubicacion_almacen">Ubicación en Almacén</Label>
                <Input
                  id="ubicacion_almacen"
                  value={formData.ubicacion_almacen}
                  onChange={(e) => setFormData({ ...formData, ubicacion_almacen: e.target.value })}
                  placeholder="Ej: Estante A, Rack 3..."
                />
              </div>

              {/* Distribuir stock inicial a depósitos */}
              <div className="space-y-3 border-t pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Distribuir stock a depósitos (opcional)</Label>
                    <p className="text-xs text-muted-foreground">
                      Carga inicial directa a depósitos/subdepósitos de clientes.
                      Se suma además del stock global.
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      setDestinosIniciales((prev) => [
                        ...prev,
                        { deposito_id: '', cantidad: '' },
                      ])
                    }
                  >
                    <Plus className="h-4 w-4 mr-1" /> Agregar
                  </Button>
                </div>

                {destinosIniciales.map((destino, idx) => (
                  <div key={idx} className="border rounded-md p-3 space-y-3 bg-muted/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground">
                        Destino #{idx + 1}
                      </span>
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7"
                        onClick={() =>
                          setDestinosIniciales((prev) =>
                            prev.filter((_, i) => i !== idx)
                          )
                        }
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                    <DepositoSelector
                      value={destino.deposito_id}
                      onChange={(id) =>
                        setDestinosIniciales((prev) =>
                          prev.map((d, i) =>
                            i === idx ? { ...d, deposito_id: id } : d
                          )
                        )
                      }
                    />
                    <div className="space-y-2">
                      <Label>Cantidad ({formData.unidad})</Label>
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={destino.cantidad}
                        onChange={(e) =>
                          setDestinosIniciales((prev) =>
                            prev.map((d, i) =>
                              i === idx ? { ...d, cantidad: e.target.value } : d
                            )
                          )
                        }
                        placeholder="0.00"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending || !formData.codigo || !formData.nombre}>
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Crear Material
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Transferir a depósito dialog */}
      <Dialog open={isTransferirOpen} onOpenChange={setIsTransferirOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ArrowRightLeft className="h-5 w-5 text-blue-600" />
              Transferir a depósito
            </DialogTitle>
            <DialogDescription>
              {selectedMaterial?.nombre} — Stock global: {selectedMaterial?.stock_actual}{' '}
              {selectedMaterial?.unidad}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <DepositoSelector
              value={transferirDepositoId}
              onChange={setTransferirDepositoId}
            />
            <div className="space-y-2">
              <Label>Cantidad ({selectedMaterial?.unidad})</Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={transferirCantidad}
                onChange={(e) => setTransferirCantidad(e.target.value)}
                placeholder="0.00"
              />
            </div>
            <div className="space-y-2">
              <Label>Motivo (opcional)</Label>
              <Input
                value={transferirMotivo}
                onChange={(e) => setTransferirMotivo(e.target.value)}
                placeholder="Ej: Carga para obra X"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsTransferirOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleTransferir}
              disabled={
                !transferirDepositoId ||
                !transferirCantidad ||
                parseFloat(transferirCantidad) <= 0 ||
                (selectedMaterial &&
                  parseFloat(transferirCantidad) > selectedMaterial.stock_actual) ||
                transferirMutation.isPending
              }
            >
              {transferirMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Transferir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Movimiento dialog */}
      <Dialog open={isMovimientoOpen} onOpenChange={setIsMovimientoOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {movimientoTipo === 'entrada' ? 'Registrar Entrada' : 'Registrar Salida'}
            </DialogTitle>
            <DialogDescription>
              {selectedMaterial?.nombre} - Stock actual: {selectedMaterial?.stock_actual}{' '}
              {selectedMaterial?.unidad}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Cantidad ({selectedMaterial?.unidad})</Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={movimientoCantidad}
                onChange={(e) => setMovimientoCantidad(e.target.value)}
                placeholder="0.00"
              />
            </div>
            <div className="space-y-2">
              <Label>Motivo (opcional)</Label>
              <Input
                value={movimientoMotivo}
                onChange={(e) => setMovimientoMotivo(e.target.value)}
                placeholder="Ej: Compra, Uso en proyecto..."
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsMovimientoOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleMovimiento}
              disabled={
                !movimientoCantidad ||
                parseFloat(movimientoCantidad) <= 0 ||
                entradaMutation.isPending ||
                salidaMutation.isPending
              }
              className={movimientoTipo === 'entrada' ? 'bg-green-600 hover:bg-green-700' : ''}
              variant={movimientoTipo === 'salida' ? 'destructive' : 'default'}
            >
              {movimientoTipo === 'entrada' ? 'Registrar Entrada' : 'Registrar Salida'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Historial dialog */}
      <Dialog open={isHistorialOpen} onOpenChange={setIsHistorialOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Historial de Movimientos
            </DialogTitle>
            <DialogDescription>
              {selectedMaterial?.nombre} - Stock actual: {selectedMaterial?.stock_actual}{' '}
              {selectedMaterial?.unidad}
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="h-[400px] pr-4">
            {isLoadingMovimientos ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : movimientos?.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No hay movimientos registrados</p>
              </div>
            ) : (
              <div className="space-y-4">
                {movimientos?.map((mov) => (
                  <div
                    key={mov.id}
                    className="flex items-start gap-4 p-3 rounded-lg border bg-card"
                  >
                    <div
                      className={`p-2 rounded-full ${
                        mov.tipo === 'entrada'
                          ? 'bg-green-100 text-green-600'
                          : mov.tipo === 'salida'
                          ? 'bg-red-100 text-red-600'
                          : 'bg-blue-100 text-blue-600'
                      }`}
                    >
                      {mov.tipo === 'entrada' ? (
                        <TrendingUp className="h-4 w-4" />
                      ) : mov.tipo === 'salida' ? (
                        <TrendingDown className="h-4 w-4" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-medium capitalize">{mov.tipo}</span>
                        <span
                          className={`font-bold ${
                            mov.tipo === 'entrada'
                              ? 'text-green-600'
                              : mov.tipo === 'salida'
                              ? 'text-red-600'
                              : ''
                          }`}
                        >
                          {mov.tipo === 'entrada' ? '+' : '-'}
                          {mov.cantidad} {selectedMaterial?.unidad}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                        <span>
                          Stock: {mov.stock_anterior} → {mov.stock_nuevo}
                        </span>
                      </div>
                      {mov.motivo && (
                        <p className="text-sm mt-1">{mov.motivo}</p>
                      )}
                      {mov.proyecto_nombre && (
                        <Badge variant="outline" className="mt-1">
                          {mov.proyecto_nombre}
                        </Badge>
                      )}
                      <p className="text-xs text-muted-foreground mt-2">
                        {formatDate(mov.created_at)}
                        {mov.usuario_nombre && ` - ${mov.usuario_nombre}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsHistorialOpen(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
