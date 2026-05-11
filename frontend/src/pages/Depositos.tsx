import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Edit,
  Trash2,
  Loader2,
  Warehouse,
  Package,
  Building2,
  Search,
  Check,
  X,
  ArrowLeft,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import {
  depositosService,
  type Deposito,
  type DepositoDetail,
} from '@/services/depositos'
import { getClientes, type ClienteListItem } from '@/services/clientes'
import { materialesService } from '@/services/materiales'

interface DepositoFormData {
  cliente_id: string
  nombre: string
  direccion: string
  descripcion: string
}

const formInicialDeposito: DepositoFormData = {
  cliente_id: '',
  nombre: '',
  direccion: '',
  descripcion: '',
}

export function DepositosPage() {
  const { toast } = useToast()
  const qc = useQueryClient()

  const [clienteFilter, setClienteFilter] = useState<string>('todos')
  const [search, setSearch] = useState('')

  // Crear/editar deposito
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingDeposito, setEditingDeposito] = useState<Deposito | null>(null)
  const [formData, setFormData] = useState<DepositoFormData>(formInicialDeposito)
  // Si se esta creando un subdeposito, el id del padre.
  const [parentForNewSubdeposito, setParentForNewSubdeposito] = useState<string | null>(null)

  // Eliminar deposito
  const [depositoToDelete, setDepositoToDelete] = useState<Deposito | null>(null)

  // Ver/gestionar materiales del deposito
  const [openDepositoId, setOpenDepositoId] = useState<string | null>(null)

  // Form para agregar material al deposito
  const [addMaterialOpen, setAddMaterialOpen] = useState(false)
  const [newMaterial, setNewMaterial] = useState({
    material_id: '',
    stock_actual: '0',
    stock_minimo: '0',
  })

  // Stock inline editing
  const [editingStock, setEditingStock] = useState<string | null>(null)
  const [stockDraft, setStockDraft] = useState('')

  const { data: clientes = [] } = useQuery({
    queryKey: ['clientes'],
    queryFn: () => getClientes(),
  })

  const { data: depositos = [], isLoading } = useQuery({
    queryKey: ['depositos', clienteFilter],
    queryFn: () =>
      depositosService.list(clienteFilter !== 'todos' ? clienteFilter : undefined),
  })

  const { data: depositoDetail } = useQuery({
    queryKey: ['deposito', openDepositoId],
    queryFn: () => depositosService.get(openDepositoId!),
    enabled: !!openDepositoId,
  })

  const { data: materialesCatalogo = [], error: materialesError } = useQuery({
    queryKey: ['materiales-catalogo'],
    queryFn: () => materialesService.getMateriales({ limit: 1000 }),
    enabled: addMaterialOpen,
    retry: false,
  })

  const createMutation = useMutation({
    mutationFn: depositosService.create,
    onSuccess: (creado) => {
      qc.invalidateQueries({ queryKey: ['depositos'] })
      // Si era un subdeposito, refrescar el padre
      if (creado.parent_id) {
        qc.invalidateQueries({ queryKey: ['deposito', creado.parent_id] })
      }
      toast({ title: creado.parent_id ? 'Subdeposito creado' : 'Deposito creado' })
      closeForm()
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al crear deposito',
        description: e?.response?.data?.detail || '',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      depositosService.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['depositos'] })
      toast({ title: 'Deposito actualizado' })
      closeForm()
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al actualizar' }),
  })

  const deleteMutation = useMutation({
    mutationFn: depositosService.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['depositos'] })
      toast({ title: 'Deposito eliminado' })
      setDepositoToDelete(null)
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al eliminar' }),
  })

  const addMaterialMutation = useMutation({
    mutationFn: ({ depositoId, data }: { depositoId: string; data: any }) =>
      depositosService.addMaterial(depositoId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['deposito', openDepositoId] })
      qc.invalidateQueries({ queryKey: ['depositos'] })
      toast({ title: 'Material agregado' })
      setAddMaterialOpen(false)
      setNewMaterial({ material_id: '', stock_actual: '0', stock_minimo: '0' })
    },
    onError: (e: any) =>
      toast({
        variant: 'destructive',
        title: 'Error al agregar material',
        description: e?.response?.data?.detail || '',
      }),
  })

  const updateStockMutation = useMutation({
    mutationFn: ({
      depositoId,
      materialId,
      stock,
    }: {
      depositoId: string
      materialId: string
      stock: number
    }) =>
      depositosService.updateMaterial(depositoId, materialId, { stock_actual: stock }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['deposito', openDepositoId] })
      setEditingStock(null)
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al actualizar stock' }),
  })

  const removeMaterialMutation = useMutation({
    mutationFn: ({
      depositoId,
      materialId,
    }: {
      depositoId: string
      materialId: string
    }) => depositosService.removeMaterial(depositoId, materialId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['deposito', openDepositoId] })
      qc.invalidateQueries({ queryKey: ['depositos'] })
      toast({ title: 'Material quitado del deposito' })
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al quitar material' }),
  })

  const openCreate = () => {
    setEditingDeposito(null)
    setFormData(formInicialDeposito)
    setIsFormOpen(true)
  }

  const openEdit = (d: Deposito) => {
    setEditingDeposito(d)
    setFormData({
      cliente_id: d.cliente_id,
      nombre: d.nombre,
      direccion: d.direccion || '',
      descripcion: d.descripcion || '',
    })
    setIsFormOpen(true)
  }

  const closeForm = () => {
    setIsFormOpen(false)
    setEditingDeposito(null)
    setParentForNewSubdeposito(null)
    setFormData(formInicialDeposito)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.nombre.trim() || !formData.cliente_id) return
    if (editingDeposito) {
      updateMutation.mutate({
        id: editingDeposito.id,
        data: {
          nombre: formData.nombre,
          direccion: formData.direccion || undefined,
          descripcion: formData.descripcion || undefined,
        },
      })
    } else {
      createMutation.mutate({
        cliente_id: formData.cliente_id,
        nombre: formData.nombre,
        direccion: formData.direccion || undefined,
        descripcion: formData.descripcion || undefined,
        parent_id: parentForNewSubdeposito || undefined,
      })
    }
  }

  const filtered = depositos.filter(
    (d) =>
      d.nombre.toLowerCase().includes(search.toLowerCase()) ||
      d.cliente_nombre?.toLowerCase().includes(search.toLowerCase())
  )

  // Materiales que aun no estan en el deposito (para selector)
  const materialesIdsEnDeposito = new Set(
    depositoDetail?.materiales.map((m) => m.material_id) || []
  )
  const materialesDisponibles = materialesCatalogo.filter(
    (m) => !materialesIdsEnDeposito.has(m.id)
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">Depositos</h1>
          <p className="text-muted-foreground">
            Gestion de depositos y stock por cliente
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Deposito
        </Button>
      </div>

      {/* Filtros */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar depositos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={clienteFilter} onValueChange={setClienteFilter}>
          <SelectTrigger className="w-full sm:w-[260px]">
            <Building2 className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Cliente" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los clientes</SelectItem>
            {clientes.map((c: ClienteListItem) => (
              <SelectItem key={c.id} value={c.id}>
                {c.nombre_fantasia || c.razon_social}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Listado */}
      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Warehouse className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">
              {search || clienteFilter !== 'todos'
                ? 'No se encontraron depositos con esos criterios'
                : 'No hay depositos cargados'}
            </p>
            <Button variant="outline" onClick={openCreate}>
              <Plus className="h-4 w-4 mr-2" />
              Crear primer deposito
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((d) => (
            <Card key={d.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Warehouse className="h-4 w-4 text-primary" />
                    {d.nombre}
                  </CardTitle>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => openEdit(d)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive"
                      onClick={() => setDepositoToDelete(d)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                {d.cliente_nombre && (
                  <CardDescription className="flex items-center gap-1">
                    <Building2 className="h-3 w-3" />
                    {d.cliente_nombre}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {d.direccion && (
                  <p className="text-sm text-muted-foreground truncate">{d.direccion}</p>
                )}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1 flex-wrap">
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <Package className="h-3 w-3" />
                      {d.cantidad_materiales} materiales
                    </Badge>
                    {d.cantidad_subdepositos > 0 && (
                      <Badge variant="outline" className="flex items-center gap-1">
                        <Warehouse className="h-3 w-3" />
                        {d.cantidad_subdepositos} subdep.
                      </Badge>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setOpenDepositoId(d.id)}
                  >
                    Ver stock
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Dialog crear/editar deposito */}
      <Dialog open={isFormOpen} onOpenChange={(o) => !o && closeForm()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingDeposito
                ? 'Editar Deposito'
                : parentForNewSubdeposito
                  ? 'Nuevo Subdeposito'
                  : 'Nuevo Deposito'}
            </DialogTitle>
            <DialogDescription>
              {editingDeposito
                ? 'Modifica los datos del deposito'
                : parentForNewSubdeposito
                  ? 'Cargar un subdeposito dentro del deposito principal'
                  : 'Cargar un nuevo deposito asociado a un cliente'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Cliente *</Label>
              <Select
                value={formData.cliente_id}
                onValueChange={(v) => setFormData({ ...formData, cliente_id: v })}
                disabled={!!editingDeposito || !!parentForNewSubdeposito}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar cliente" />
                </SelectTrigger>
                <SelectContent>
                  {clientes.map((c: ClienteListItem) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.nombre_fantasia || c.razon_social}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Nombre *</Label>
              <Input
                value={formData.nombre}
                onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                placeholder="Ej: Deposito Central"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Direccion</Label>
              <Input
                value={formData.direccion}
                onChange={(e) => setFormData({ ...formData, direccion: e.target.value })}
                placeholder="Direccion del deposito"
              />
            </div>
            <div className="space-y-2">
              <Label>Descripcion</Label>
              <Textarea
                value={formData.descripcion}
                onChange={(e) =>
                  setFormData({ ...formData, descripcion: e.target.value })
                }
                rows={2}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeForm}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={
                  !formData.nombre.trim() ||
                  !formData.cliente_id ||
                  createMutation.isPending ||
                  updateMutation.isPending
                }
              >
                {(createMutation.isPending || updateMutation.isPending) && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {editingDeposito ? 'Guardar' : 'Crear'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog confirmar eliminacion */}
      <Dialog
        open={!!depositoToDelete}
        onOpenChange={(o) => !o && setDepositoToDelete(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar deposito</DialogTitle>
            <DialogDescription>
              Vas a eliminar <strong>{depositoToDelete?.nombre}</strong>. Esta accion
              tambien elimina sus materiales y stock asociado.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDepositoToDelete(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                depositoToDelete && deleteMutation.mutate(depositoToDelete.id)
              }
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog gestionar materiales del deposito */}
      <Dialog
        open={!!openDepositoId}
        onOpenChange={(o) => !o && setOpenDepositoId(null)}
      >
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Warehouse className="h-5 w-5 text-primary" />
              {depositoDetail ? depositoDetail.nombre : 'Cargando...'}
              {depositoDetail?.parent_id && (
                <Badge variant="outline" className="text-xs">subdeposito</Badge>
              )}
            </DialogTitle>
            <DialogDescription>
              {depositoDetail?.cliente_nombre && (
                <span className="flex items-center gap-1">
                  <Building2 className="h-3 w-3" />
                  {depositoDetail.cliente_nombre}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {/* Resumen total agregado (deposito + subdepositos) */}
          {depositoDetail && depositoDetail.subdepositos.length > 0 && (
            <div className="border rounded-md p-3 bg-muted/30 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">
                  Resumen total (deposito + subdepositos)
                </p>
                <Badge variant="secondary">
                  {depositoDetail.materiales_totales.length} materiales
                </Badge>
              </div>
              {depositoDetail.materiales_totales.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material</TableHead>
                      <TableHead className="text-right">Stock total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {depositoDetail.materiales_totales.map((m) => (
                      <TableRow key={m.material_id}>
                        <TableCell>
                          <div className="font-medium">{m.material_nombre}</div>
                          <div className="text-xs text-muted-foreground">
                            {m.material_codigo}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {Number(m.stock_total).toFixed(2)} {m.material_unidad}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-xs text-muted-foreground">
                  Aun no hay materiales cargados.
                </p>
              )}
            </div>
          )}

          {/* Subdepositos */}
          {depositoDetail && !depositoDetail.parent_id && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">
                  Subdepositos
                  {depositoDetail.subdepositos.length > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {depositoDetail.subdepositos.length}
                    </Badge>
                  )}
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditingDeposito(null)
                    setFormData({
                      cliente_id: depositoDetail.cliente_id,
                      nombre: '',
                      direccion: '',
                      descripcion: '',
                    })
                    setParentForNewSubdeposito(depositoDetail.id)
                    setIsFormOpen(true)
                  }}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Nuevo subdeposito
                </Button>
              </div>
              {depositoDetail.subdepositos.length === 0 ? (
                <p className="text-xs text-muted-foreground py-2">
                  Sin subdepositos cargados.
                </p>
              ) : (
                <div className="grid gap-2 md:grid-cols-2">
                  {depositoDetail.subdepositos.map((sub) => (
                    <div
                      key={sub.id}
                      className="flex items-center justify-between p-3 border rounded-md hover:bg-muted/50"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{sub.nombre}</p>
                        <p className="text-xs text-muted-foreground">
                          {sub.cantidad_materiales} materiales
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => setOpenDepositoId(sub.id)}
                          title="Ver stock del subdeposito"
                        >
                          <Package className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => setDepositoToDelete(sub)}
                          title="Eliminar subdeposito"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Si es subdeposito, mostrar boton para volver al padre */}
          {depositoDetail?.parent_id && (
            <Button
              variant="outline"
              size="sm"
              className="self-start"
              onClick={() => setOpenDepositoId(depositoDetail.parent_id!)}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Volver al deposito principal
            </Button>
          )}

          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">
              Materiales directos
              {depositoDetail && (
                <span className="text-xs text-muted-foreground ml-2">
                  ({depositoDetail.materiales.length})
                </span>
              )}
            </p>
            <Button
              size="sm"
              onClick={() => {
                setNewMaterial({ material_id: '', stock_actual: '0', stock_minimo: '0' })
                setAddMaterialOpen(true)
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Agregar material
            </Button>
          </div>

          {depositoDetail && depositoDetail.materiales.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Package className="h-10 w-10 mx-auto mb-2 opacity-50" />
              Este deposito no tiene materiales cargados todavia
            </div>
          ) : depositoDetail ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Material</TableHead>
                  <TableHead className="text-right">Stock actual</TableHead>
                  <TableHead className="w-[80px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {depositoDetail.materiales.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell>
                      <div className="font-medium">{m.material_nombre}</div>
                      <div className="text-xs text-muted-foreground">
                        {m.material_codigo} • {m.material_unidad}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {editingStock === m.id ? (
                        <div className="flex items-center justify-end gap-2">
                          <Input
                            type="number"
                            step="0.01"
                            min="0"
                            className="h-8 w-24"
                            value={stockDraft}
                            onChange={(e) => setStockDraft(e.target.value)}
                            autoFocus
                          />
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7"
                            onClick={() =>
                              updateStockMutation.mutate({
                                depositoId: openDepositoId!,
                                materialId: m.material_id,
                                stock: parseFloat(stockDraft) || 0,
                              })
                            }
                          >
                            <Check className="h-4 w-4 text-green-600" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7"
                            onClick={() => setEditingStock(null)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="hover:underline"
                          onClick={() => {
                            setEditingStock(m.id)
                            setStockDraft(String(m.stock_actual))
                          }}
                        >
                          {Number(m.stock_actual).toFixed(2)} {m.material_unidad}
                        </button>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive"
                        onClick={() =>
                          removeMaterialMutation.mutate({
                            depositoId: openDepositoId!,
                            materialId: m.material_id,
                          })
                        }
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog agregar material al deposito */}
      <Dialog open={addMaterialOpen} onOpenChange={setAddMaterialOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agregar material al deposito</DialogTitle>
            <DialogDescription>
              Selecciona un material del catalogo y carga su stock inicial.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Material *</Label>
              <Select
                value={newMaterial.material_id}
                onValueChange={(v) =>
                  setNewMaterial({ ...newMaterial, material_id: v })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar material" />
                </SelectTrigger>
                <SelectContent>
                  {materialesError ? (
                    <div className="p-2 text-sm text-destructive text-center">
                      Error al cargar el catalogo
                    </div>
                  ) : materialesCatalogo.length === 0 ? (
                    <div className="p-2 text-sm text-muted-foreground text-center">
                      No hay materiales en el catalogo. Crealos primero en
                      Recursos &gt; Materiales.
                    </div>
                  ) : materialesDisponibles.length === 0 ? (
                    <div className="p-2 text-sm text-muted-foreground text-center">
                      Todos los materiales del catalogo ya estan en este deposito
                    </div>
                  ) : (
                    materialesDisponibles.map((m) => (
                      <SelectItem key={m.id} value={m.id}>
                        {m.nombre} ({m.unidad})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Stock actual</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={newMaterial.stock_actual}
                  onChange={(e) =>
                    setNewMaterial({ ...newMaterial, stock_actual: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Stock minimo</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={newMaterial.stock_minimo}
                  onChange={(e) =>
                    setNewMaterial({ ...newMaterial, stock_minimo: e.target.value })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddMaterialOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={() =>
                addMaterialMutation.mutate({
                  depositoId: openDepositoId!,
                  data: {
                    material_id: newMaterial.material_id,
                    stock_actual: parseFloat(newMaterial.stock_actual) || 0,
                    stock_minimo: parseFloat(newMaterial.stock_minimo) || 0,
                  },
                })
              }
              disabled={!newMaterial.material_id || addMaterialMutation.isPending}
            >
              {addMaterialMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Agregar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
