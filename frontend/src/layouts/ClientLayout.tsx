import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { FolderKanban, Image, FileText, LogOut, User } from 'lucide-react'
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
import { useAuthStore, useUser } from '@/store/auth'

const navigation = [
  { name: 'Mis Proyectos', href: '/portal', icon: FolderKanban },
]

export function ClientLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useUser()
  const logout = useAuthStore((state) => state.logout)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userInitials = user
    ? `${user.nombre.charAt(0)}${user.apellido.charAt(0)}`.toUpperCase()
    : 'C'

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-card border-b">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <Link to="/portal" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-electroamerica-red rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">EA</span>
              </div>
              <span className="font-semibold text-lg hidden sm:block">
                Electro América
              </span>
            </Link>

            <nav className="flex items-center gap-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href ||
                  location.pathname.startsWith(item.href + '/')

                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    <span className="hidden sm:inline">{item.name}</span>
                  </Link>
                )
              })}
            </nav>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                      {userInitials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden sm:inline text-sm">
                    {user?.nombre}
                  </span>
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
                <DropdownMenuItem onClick={() => navigate('/portal/perfil')}>
                  <User className="mr-2 h-4 w-4" />
                  Mi Perfil
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  Cerrar sesión
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t mt-auto">
        <div className="container mx-auto px-4 py-4">
          <p className="text-center text-sm text-muted-foreground">
            Portal del Cliente - Electro América
          </p>
        </div>
      </footer>
    </div>
  )
}
