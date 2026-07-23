import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  Package,
  Wrench,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Wallet,
  Building2,
  FileBarChart,
  AlertCircle,
  Activity,
  Clock,
  Calendar,
  PlayCircle,
  History,
  ClipboardList,
  HardHat,
  Truck,
  DollarSign,
  Shield,
  Hammer,
  HandCoins,
  ClipboardCheck,
  Warehouse,
  FileText,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { useAuthStore, useUser, useModulosEfectivos } from '@/store/auth'
import { AlertasDropdown } from '@/components/AlertasDropdown'

type RolUsuario = 'administrador' | 'supervisor' | 'operario' | 'cliente'

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  roles: RolUsuario[]
  modulo?: string // Módulo requerido para ver este item
}

interface NavSection {
  title: string
  icon: React.ComponentType<{ className?: string }>
  roles: RolUsuario[]
  items: NavItem[]
  modulo?: string // Módulo requerido para ver toda la sección
}

const navigationSections: NavSection[] = [
  {
    title: 'General',
    icon: LayoutDashboard,
    roles: ['administrador', 'supervisor', 'operario'],
    modulo: 'dashboard',
    items: [
      { name: 'Dashboard', href: '/', icon: LayoutDashboard, roles: ['administrador', 'supervisor', 'operario'], modulo: 'dashboard' },
    ],
  },
  {
    title: 'Producción',
    icon: HardHat,
    roles: ['administrador', 'supervisor', 'operario'],
    items: [
      { name: 'Proyectos', href: '/proyectos', icon: FolderKanban, roles: ['administrador', 'supervisor', 'operario'], modulo: 'proyectos' },
      { name: 'Clientes', href: '/clientes', icon: Building2, roles: ['administrador', 'supervisor'], modulo: 'clientes' },
    ],
  },
  {
    title: 'Mi Jornada',
    icon: Clock,
    roles: ['operario'],
    modulo: 'jornadas_operario',
    items: [
      { name: 'Fichar Entrada/Salida', href: '/operario/fichaje', icon: Clock, roles: ['operario'], modulo: 'jornadas_operario' },
      { name: 'Iniciar Jornada', href: '/operario/iniciar-jornada', icon: PlayCircle, roles: ['operario'], modulo: 'jornadas_operario' },
      { name: 'Jornada Activa', href: '/operario/jornada-activa', icon: Clock, roles: ['operario'], modulo: 'jornadas_operario' },
      { name: 'Mi Historial', href: '/operario/historial', icon: History, roles: ['operario'], modulo: 'jornadas_operario' },
    ],
  },
  {
    title: 'Gestión de Jornadas',
    icon: Calendar,
    roles: ['administrador', 'supervisor'],
    modulo: 'jornadas_gestion',
    items: [
      { name: 'Monitor Jornadas', href: '/jornadas/monitor', icon: Clock, roles: ['administrador', 'supervisor'], modulo: 'jornadas_gestion' },
      { name: 'Fichajes', href: '/jornadas/fichajes', icon: ClipboardCheck, roles: ['administrador', 'supervisor'], modulo: 'jornadas_gestion' },
      { name: 'Planificación', href: '/jornadas/planificacion', icon: Calendar, roles: ['administrador', 'supervisor'], modulo: 'jornadas_gestion' },
      { name: 'Tareas', href: '/actividades-tipo', icon: ClipboardList, roles: ['administrador', 'supervisor'], modulo: 'actividades_tipo' },
    ],
  },
  {
    title: 'Recursos',
    icon: Truck,
    roles: ['administrador', 'supervisor', 'operario'],
    items: [
      { name: 'Materiales', href: '/materiales', icon: Package, roles: ['administrador', 'supervisor', 'operario'], modulo: 'materiales' },
      { name: 'Depositos', href: '/depositos', icon: Warehouse, roles: ['administrador', 'supervisor'], modulo: 'depositos' },
      { name: 'Remitos', href: '/remitos', icon: FileText, roles: ['administrador', 'supervisor'], modulo: 'remitos' },
      { name: 'Equipos', href: '/equipos', icon: Wrench, roles: ['administrador', 'supervisor', 'operario'], modulo: 'equipos' },
    ],
  },
  {
    title: 'Herramientas',
    icon: Hammer,
    roles: ['administrador', 'supervisor'],
    modulo: 'herramientas',
    items: [
      { name: 'Control Préstamos', href: '/herramientas/prestamos', icon: HandCoins, roles: ['administrador', 'supervisor'], modulo: 'herramientas' },
      { name: 'Inventario', href: '/herramientas/inventario', icon: ClipboardCheck, roles: ['administrador', 'supervisor'], modulo: 'herramientas' },
    ],
  },
  {
    title: 'Finanzas',
    icon: DollarSign,
    roles: ['administrador', 'supervisor'],
    modulo: 'finanzas',
    items: [
      { name: 'Resumen Financiero', href: '/finanzas', icon: Wallet, roles: ['administrador', 'supervisor'], modulo: 'finanzas' },
      { name: 'Panel de Socios', href: '/panel-socios', icon: Users, roles: ['administrador', 'supervisor'], modulo: 'finanzas' },
      { name: 'Reportes', href: '/reportes', icon: FileBarChart, roles: ['administrador', 'supervisor'], modulo: 'reportes' },
    ],
  },
  {
    title: 'Administración',
    icon: Shield,
    roles: ['administrador'],
    items: [
      { name: 'Usuarios', href: '/usuarios', icon: Users, roles: ['administrador'], modulo: 'usuarios' },
      { name: 'Alertas', href: '/alertas', icon: AlertCircle, roles: ['administrador', 'supervisor'], modulo: 'alertas' },
      { name: 'Auditoría', href: '/auditoria', icon: Activity, roles: ['administrador'], modulo: 'auditoria' },
    ],
  },
]

export function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const user = useUser()
  const modulosEfectivos = useModulosEfectivos()
  const logout = useAuthStore((state) => state.logout)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Helper para verificar si tiene acceso a un módulo
  const tieneAccesoModulo = (modulo?: string) => {
    if (!modulo) return true // Si no tiene módulo definido, mostrar siempre
    return modulosEfectivos.includes(modulo)
  }

  // Filtrar secciones y sus items según el rol del usuario Y sus módulos permitidos
  const filteredSections = navigationSections
    .filter((section) => {
      // Verificar rol
      if (!user || !section.roles.includes(user.rol)) return false
      // Verificar módulo de la sección (si tiene)
      if (section.modulo && !tieneAccesoModulo(section.modulo)) return false
      return true
    })
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        // Verificar rol
        if (!user || !item.roles.includes(user.rol)) return false
        // Verificar módulo del item
        if (!tieneAccesoModulo(item.modulo)) return false
        return true
      }),
    }))
    .filter((section) => section.items.length > 0)

  const userInitials = user
    ? `${user.nombre.charAt(0)}${user.apellido.charAt(0)}`.toUpperCase()
    : 'U'

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-card border-r transform transition-transform duration-200 ease-in-out lg:translate-x-0 flex flex-col',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b">
          <Link to="/" className="flex items-center">
            <img
              src="/logo.jpg"
              alt="Electro América"
              className="h-10 w-auto"
            />
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="flex-1 overflow-y-auto px-2 py-4">
          {filteredSections.map((section, sectionIndex) => (
            <div key={section.title} className={cn(sectionIndex > 0 && 'mt-4')}>
              {/* Section header */}
              <div className="flex items-center gap-2 px-3 py-2">
                <section.icon className="h-4 w-4 text-gray-700" />
                <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  {section.title}
                </span>
              </div>

              {/* Section items */}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const isActive = location.pathname === item.href ||
                    (item.href !== '/' && location.pathname.startsWith(item.href))

                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ml-2',
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.name}
                    </Link>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t p-4 mt-auto">
          <div className="flex items-center gap-3">
            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.nombre} {user?.apellido}
              </p>
              <p className="text-xs text-muted-foreground capitalize">
                {user?.rol}
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top navbar */}
        <header className="sticky top-0 z-30 h-16 bg-card border-b flex items-center justify-between px-4 lg:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex-1" />

          <div className="flex items-center gap-2">
            <AlertasDropdown />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                      {userInitials}
                    </AvatarFallback>
                  </Avatar>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span>{user?.nombre} {user?.apellido}</span>
                    <span className="text-xs text-muted-foreground font-normal">
                      {user?.email}
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/perfil')}>
                  <Settings className="mr-2 h-4 w-4" />
                  Configuración
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  Cerrar sesión
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
