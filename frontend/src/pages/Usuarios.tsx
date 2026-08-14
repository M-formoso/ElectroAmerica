import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  UserCheck,
  UserX,
  Loader2,
  Mail,
  Phone,
  Shield,
  Settings,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ViewToggle, type ViewMode } from '@/components/ui/view-toggle'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { usuariosService, type Usuario, type UsuarioCreate, moduloLabels } from '@/services/usuarios'
import { useToast } from '@/hooks/use-toast'
import { useIsSuperadmin } from '@/store/auth'

const rolColors: Record<string, string> = {
  administrador: 'destructive',
  supervisor: 'default',
  operario: 'secondary',
  cliente: 'outline',
}

const rolLabels: Record<string, string> = {
  administrador: 'Administrador',
  supervisor: 'Supervisor',
  operario: 'Operario',
  cliente: 'Cliente',
}

// Módulos disponibles en el sistema
const MODULOS_DISPONIBLES = [
  'dashboard',
  'proyectos',
  'clientes',
  'materiales',
  'depositos',
  'remitos',
  'equipos',
  'herramientas',
  'finanzas',
  'reportes',
  'facturas_cobrar',
  'usuarios',
  'alertas',
  'auditoria',
  'jornadas_operario',
  'jornadas_gestion',
  'actividades_tipo',
]

// Módulos por defecto según rol
const MODULOS_POR_ROL: Record<string, string[]> = {
  administrador: MODULOS_DISPONIBLES,
  supervisor: [
    'dashboard', 'proyectos', 'clientes', 'materiales', 'depositos', 'remitos',
    'equipos', 'herramientas', 'finanzas', 'reportes', 'facturas_cobrar', 'alertas',
    'jornadas_gestion', 'actividades_tipo'
  ],
  operario: [
    'dashboard', 'proyectos', 'materiales', 'equipos',
    'jornadas_operario'
  ],
  cliente: []
}

interface UsuarioForm {
  email: string
  password: string
  nombre: string
  apellido: string
  telefono: string
  rol: string
  es_superadmin: boolean
  modulos_permitidos: string[]
  usar_modulos_personalizados: boolean
}

const initialFormState: UsuarioForm = {
  email: '',
  password: '',
  nombre: '',
  apellido: '',
  telefono: '',
  rol: 'operario',
  es_superadmin: false,
  modulos_permitidos: [],
  usar_modulos_personalizados: false,
}

export function UsuariosPage() {
  const [search, setSearch] = useState('')
  const [rolFilter, setRolFilter] = useState<string>('todos')
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [selectedUsuario, setSelectedUsuario] = useState<Usuario | null>(null)
  const [formData, setFormData] = useState<UsuarioForm>(initialFormState)
  const [activeTab, setActiveTab] = useState('datos')

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isSuperadmin = useIsSuperadmin()

  // Cuando cambia el rol, actualizar módulos por defecto
  useEffect(() => {
    if (!formData.usar_modulos_personalizados) {
      setFormData(prev => ({
        ...prev,
        modulos_permitidos: MODULOS_POR_ROL[prev.rol] || []
      }))
    }
  }, [formData.rol, formData.usar_modulos_personalizados])

  const { data: usuarios, isLoading } = useQuery({
    queryKey: ['usuarios', rolFilter],
    queryFn: () => usuariosService.getUsuarios(
      rolFilter !== 'todos' ? { rol: rolFilter } : undefined
    ),
  })

  const createMutation = useMutation({
    mutationFn: usuariosService.createUsuario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      toast({ title: 'Usuario creado exitosamente' })
      setIsCreateOpen(false)
      setFormData(initialFormState)
      setActiveTab('datos')
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al crear usuario',
        description: error.response?.data?.detail || 'Error desconocido',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      usuariosService.updateUsuario(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      toast({ title: 'Usuario actualizado exitosamente' })
      setIsEditOpen(false)
      setSelectedUsuario(null)
      setFormData(initialFormState)
      setActiveTab('datos')
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al actualizar usuario',
        description: error.response?.data?.detail || 'Error desconocido',
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: usuariosService.deleteUsuario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      toast({ title: 'Usuario eliminado' })
      setIsDeleteOpen(false)
      setSelectedUsuario(null)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al eliminar usuario' })
    },
  })

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      email: formData.email,
      password: formData.password,
      nombre: formData.nombre,
      apellido: formData.apellido,
      telefono: formData.telefono || undefined,
      rol: formData.rol,
      es_superadmin: formData.es_superadmin,
      modulos_permitidos: formData.usar_modulos_personalizados ? formData.modulos_permitidos : undefined,
    })
  }

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedUsuario) return

    const updateData: any = {
      email: formData.email,
      nombre: formData.nombre,
      apellido: formData.apellido,
      telefono: formData.telefono || undefined,
      rol: formData.rol,
      es_superadmin: formData.es_superadmin,
      modulos_permitidos: formData.usar_modulos_personalizados ? formData.modulos_permitidos : null,
    }

    // Solo incluir password si se modificó
    if (formData.password) {
      updateData.password = formData.password
    }

    updateMutation.mutate({ id: selectedUsuario.id, data: updateData })
  }

  const handleOpenEdit = (usuario: Usuario) => {
    setSelectedUsuario(usuario)
    const tieneModulosPersonalizados = usuario.modulos_permitidos && usuario.modulos_permitidos.length > 0
    setFormData({
      email: usuario.email,
      password: '',
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      telefono: usuario.telefono || '',
      rol: usuario.rol,
      es_superadmin: usuario.es_superadmin,
      modulos_permitidos: usuario.modulos_permitidos || MODULOS_POR_ROL[usuario.rol] || [],
      usar_modulos_personalizados: !!tieneModulosPersonalizados,
    })
    setActiveTab('datos')
    setIsEditOpen(true)
  }

  const handleToggleModulo = (modulo: string) => {
    setFormData(prev => ({
      ...prev,
      modulos_permitidos: prev.modulos_permitidos.includes(modulo)
        ? prev.modulos_permitidos.filter(m => m !== modulo)
        : [...prev.modulos_permitidos, modulo]
    }))
  }

  const handleSelectAllModulos = () => {
    setFormData(prev => ({
      ...prev,
      modulos_permitidos: MODULOS_DISPONIBLES
    }))
  }

  const handleDeselectAllModulos = () => {
    setFormData(prev => ({
      ...prev,
      modulos_permitidos: []
    }))
  }

  const filteredUsuarios = usuarios?.filter((u) =>
    u.nombre.toLowerCase().includes(search.toLowerCase()) ||
    u.apellido.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Usuarios</h1>
          <p className="text-muted-foreground">
            Gestiona los usuarios del sistema
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Usuario
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar usuarios..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={rolFilter} onValueChange={setRolFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Rol" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los roles</SelectItem>
            <SelectItem value="administrador">Administrador</SelectItem>
            <SelectItem value="supervisor">Supervisor</SelectItem>
            <SelectItem value="operario">Operario</SelectItem>
            <SelectItem value="cliente">Cliente</SelectItem>
          </SelectContent>
        </Select>
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
          ) : filteredUsuarios?.length === 0 ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              No se encontraron usuarios
            </div>
          ) : (
            filteredUsuarios?.map((usuario) => (
              <Card key={usuario.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1 min-w-0">
                      <CardTitle className="text-lg truncate">
                        {usuario.nombre} {usuario.apellido}
                      </CardTitle>
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Mail className="h-3 w-3" />
                        {usuario.email}
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleOpenEdit(usuario)}>
                          <Edit className="h-4 w-4 mr-2" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => {
                            setSelectedUsuario(usuario)
                            setIsDeleteOpen(true)
                          }}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {usuario.telefono && (
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Phone className="h-3 w-3" />
                      {usuario.telefono}
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-2 border-t">
                    <div className="flex items-center gap-2">
                      <Badge variant={rolColors[usuario.rol] as any}>
                        {rolLabels[usuario.rol]}
                      </Badge>
                      {usuario.es_superadmin && (
                        <Badge variant="destructive" className="gap-1">
                          <Shield className="h-3 w-3" />
                          Superadmin
                        </Badge>
                      )}
                    </div>
                    {usuario.activo ? (
                      <Badge variant="success" className="gap-1">
                        <UserCheck className="h-3 w-3" />
                        Activo
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="gap-1">
                        <UserX className="h-3 w-3" />
                        Inactivo
                      </Badge>
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
              <TableHead>Nombre</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Teléfono</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-[100px]">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <TableRow key={i}>
                  {[...Array(6)].map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 bg-muted rounded animate-pulse" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : filteredUsuarios?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  No se encontraron usuarios
                </TableCell>
              </TableRow>
            ) : (
              filteredUsuarios?.map((usuario) => (
                <TableRow key={usuario.id}>
                  <TableCell>
                    <p className="font-medium">
                      {usuario.nombre} {usuario.apellido}
                    </p>
                  </TableCell>
                  <TableCell>{usuario.email}</TableCell>
                  <TableCell>{usuario.telefono || '-'}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge variant={rolColors[usuario.rol] as any}>
                        {rolLabels[usuario.rol]}
                      </Badge>
                      {usuario.es_superadmin && (
                        <Badge variant="destructive" className="gap-1">
                          <Shield className="h-3 w-3" />
                          Super
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {usuario.activo ? (
                      <Badge variant="success" className="gap-1">
                        <UserCheck className="h-3 w-3" />
                        Activo
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="gap-1">
                        <UserX className="h-3 w-3" />
                        Inactivo
                      </Badge>
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
                        <DropdownMenuItem onClick={() => handleOpenEdit(usuario)}>
                          <Edit className="h-4 w-4 mr-2" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => {
                            setSelectedUsuario(usuario)
                            setIsDeleteOpen(true)
                          }}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Eliminar
                        </DropdownMenuItem>
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

      {/* Create usuario dialog */}
      <Dialog open={isCreateOpen} onOpenChange={(open) => {
        setIsCreateOpen(open)
        if (!open) {
          setFormData(initialFormState)
          setActiveTab('datos')
        }
      }}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nuevo Usuario</DialogTitle>
            <DialogDescription>
              Ingresa los datos del nuevo usuario y configura sus permisos
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit} autoComplete="off">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="datos">Datos</TabsTrigger>
                <TabsTrigger value="permisos">Permisos</TabsTrigger>
              </TabsList>

              <TabsContent value="datos" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nombre *</Label>
                    <Input
                      value={formData.nombre}
                      onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                      placeholder="Nombre"
                      required
                      autoComplete="off"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Apellido *</Label>
                    <Input
                      value={formData.apellido}
                      onChange={(e) => setFormData({ ...formData, apellido: e.target.value })}
                      placeholder="Apellido"
                      required
                      autoComplete="off"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="email@ejemplo.com"
                    required
                    autoComplete="off"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Contraseña *</Label>
                  <Input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Mínimo 6 caracteres"
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Teléfono</Label>
                    <Input
                      value={formData.telefono}
                      onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                      placeholder="+54 9 11 1234-5678"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Rol *</Label>
                    <Select
                      value={formData.rol}
                      onValueChange={(v) => setFormData({ ...formData, rol: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="administrador">Administrador</SelectItem>
                        <SelectItem value="supervisor">Supervisor</SelectItem>
                        <SelectItem value="operario">Operario</SelectItem>
                        <SelectItem value="cliente">Cliente</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="permisos" className="space-y-4 mt-4">
                {/* Superadmin toggle */}
                {isSuperadmin && (
                  <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label className="text-base flex items-center gap-2">
                            <Shield className="h-4 w-4 text-red-600" />
                            Superadministrador
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Acceso total a todos los módulos del sistema
                          </p>
                        </div>
                        <Switch
                          checked={formData.es_superadmin}
                          onCheckedChange={(checked: boolean) => setFormData({ ...formData, es_superadmin: checked })}
                        />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {!formData.es_superadmin && (
                  <>
                    {/* Toggle permisos personalizados */}
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between">
                          <div className="space-y-0.5">
                            <Label className="text-base flex items-center gap-2">
                              <Settings className="h-4 w-4" />
                              Permisos personalizados
                            </Label>
                            <p className="text-sm text-muted-foreground">
                              {formData.usar_modulos_personalizados
                                ? 'Selecciona manualmente los módulos'
                                : `Usa permisos por defecto del rol ${rolLabels[formData.rol]}`}
                            </p>
                          </div>
                          <Switch
                            checked={formData.usar_modulos_personalizados}
                            onCheckedChange={(checked: boolean) => setFormData({
                              ...formData,
                              usar_modulos_personalizados: checked,
                              modulos_permitidos: checked ? formData.modulos_permitidos : MODULOS_POR_ROL[formData.rol] || []
                            })}
                          />
                        </div>
                      </CardContent>
                    </Card>

                    {/* Lista de módulos */}
                    <Card>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">Módulos</CardTitle>
                          {formData.usar_modulos_personalizados && (
                            <div className="flex gap-2">
                              <Button type="button" variant="outline" size="sm" onClick={handleSelectAllModulos}>
                                Todos
                              </Button>
                              <Button type="button" variant="outline" size="sm" onClick={handleDeselectAllModulos}>
                                Ninguno
                              </Button>
                            </div>
                          )}
                        </div>
                        <CardDescription>
                          {formData.modulos_permitidos.length} de {MODULOS_DISPONIBLES.length} módulos seleccionados
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-3">
                          {MODULOS_DISPONIBLES.map((modulo) => (
                            <div key={modulo} className="flex items-center space-x-2">
                              <Checkbox
                                id={`modulo-${modulo}`}
                                checked={formData.modulos_permitidos.includes(modulo)}
                                onCheckedChange={() => handleToggleModulo(modulo)}
                                disabled={!formData.usar_modulos_personalizados}
                              />
                              <label
                                htmlFor={`modulo-${modulo}`}
                                className={`text-sm font-medium leading-none peer-disabled:cursor-not-allowed ${
                                  !formData.usar_modulos_personalizados ? 'text-muted-foreground' : ''
                                }`}
                              >
                                {moduloLabels[modulo] || modulo}
                              </label>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending || !formData.email || !formData.password || !formData.nombre || !formData.apellido}
              >
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Crear Usuario
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit usuario dialog */}
      <Dialog open={isEditOpen} onOpenChange={(open) => {
        setIsEditOpen(open)
        if (!open) {
          setSelectedUsuario(null)
          setFormData(initialFormState)
          setActiveTab('datos')
        }
      }}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar Usuario</DialogTitle>
            <DialogDescription>
              Modifica los datos del usuario y sus permisos
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit}>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="datos">Datos</TabsTrigger>
                <TabsTrigger value="permisos">Permisos</TabsTrigger>
              </TabsList>

              <TabsContent value="datos" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nombre *</Label>
                    <Input
                      value={formData.nombre}
                      onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                      placeholder="Nombre"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Apellido *</Label>
                    <Input
                      value={formData.apellido}
                      onChange={(e) => setFormData({ ...formData, apellido: e.target.value })}
                      placeholder="Apellido"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="email@ejemplo.com"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Nueva contraseña (dejar vacío para no cambiar)</Label>
                  <Input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Nueva contraseña"
                    minLength={6}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Teléfono</Label>
                    <Input
                      value={formData.telefono}
                      onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                      placeholder="+54 9 11 1234-5678"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Rol *</Label>
                    <Select
                      value={formData.rol}
                      onValueChange={(v) => setFormData({ ...formData, rol: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="administrador">Administrador</SelectItem>
                        <SelectItem value="supervisor">Supervisor</SelectItem>
                        <SelectItem value="operario">Operario</SelectItem>
                        <SelectItem value="cliente">Cliente</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="permisos" className="space-y-4 mt-4">
                {/* Superadmin toggle */}
                {isSuperadmin && (
                  <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label className="text-base flex items-center gap-2">
                            <Shield className="h-4 w-4 text-red-600" />
                            Superadministrador
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Acceso total a todos los módulos del sistema
                          </p>
                        </div>
                        <Switch
                          checked={formData.es_superadmin}
                          onCheckedChange={(checked: boolean) => setFormData({ ...formData, es_superadmin: checked })}
                        />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {!formData.es_superadmin && (
                  <>
                    {/* Toggle permisos personalizados */}
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between">
                          <div className="space-y-0.5">
                            <Label className="text-base flex items-center gap-2">
                              <Settings className="h-4 w-4" />
                              Permisos personalizados
                            </Label>
                            <p className="text-sm text-muted-foreground">
                              {formData.usar_modulos_personalizados
                                ? 'Selecciona manualmente los módulos'
                                : `Usa permisos por defecto del rol ${rolLabels[formData.rol]}`}
                            </p>
                          </div>
                          <Switch
                            checked={formData.usar_modulos_personalizados}
                            onCheckedChange={(checked: boolean) => setFormData({
                              ...formData,
                              usar_modulos_personalizados: checked,
                              modulos_permitidos: checked ? formData.modulos_permitidos : MODULOS_POR_ROL[formData.rol] || []
                            })}
                          />
                        </div>
                      </CardContent>
                    </Card>

                    {/* Lista de módulos */}
                    <Card>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">Módulos</CardTitle>
                          {formData.usar_modulos_personalizados && (
                            <div className="flex gap-2">
                              <Button type="button" variant="outline" size="sm" onClick={handleSelectAllModulos}>
                                Todos
                              </Button>
                              <Button type="button" variant="outline" size="sm" onClick={handleDeselectAllModulos}>
                                Ninguno
                              </Button>
                            </div>
                          )}
                        </div>
                        <CardDescription>
                          {formData.modulos_permitidos.length} de {MODULOS_DISPONIBLES.length} módulos seleccionados
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-3">
                          {MODULOS_DISPONIBLES.map((modulo) => (
                            <div key={modulo} className="flex items-center space-x-2">
                              <Checkbox
                                id={`edit-modulo-${modulo}`}
                                checked={formData.modulos_permitidos.includes(modulo)}
                                onCheckedChange={() => handleToggleModulo(modulo)}
                                disabled={!formData.usar_modulos_personalizados}
                              />
                              <label
                                htmlFor={`edit-modulo-${modulo}`}
                                className={`text-sm font-medium leading-none peer-disabled:cursor-not-allowed ${
                                  !formData.usar_modulos_personalizados ? 'text-muted-foreground' : ''
                                }`}
                              >
                                {moduloLabels[modulo] || modulo}
                              </label>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={updateMutation.isPending || !formData.email || !formData.nombre || !formData.apellido}
              >
                {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Guardar Cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar usuario</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de eliminar a "{selectedUsuario?.nombre} {selectedUsuario?.apellido}"?
              Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => selectedUsuario && deleteMutation.mutate(selectedUsuario.id)}
              disabled={deleteMutation.isPending}
            >
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
