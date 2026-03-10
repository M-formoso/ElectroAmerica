import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Search,
  Package,
  AlertTriangle,
  ArrowUpCircle,
  ArrowDownCircle,
  MoreVertical,
  Edit,
  Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Label } from '@/components/ui/label'
import { materialesService } from '@/services/materiales'
import { formatCurrency } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import type { Material } from '@/types'

export function MaterialesPage() {
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isMovimientoOpen, setIsMovimientoOpen] = useState(false)
  const [movimientoTipo, setMovimientoTipo] = useState<'entrada' | 'salida'>('entrada')
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null)
  const [movimientoCantidad, setMovimientoCantidad] = useState('')
  const [movimientoMotivo, setMovimientoMotivo] = useState('')

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

  const resetMovimientoForm = () => {
    setMovimientoCantidad('')
    setMovimientoMotivo('')
    setSelectedMaterial(null)
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

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar por nombre o código..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Table */}
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
    </div>
  )
}
