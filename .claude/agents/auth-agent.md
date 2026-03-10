# Agente: Autenticación y Autorización

## Rol
Implementar el sistema completo de autenticación JWT, gestión de usuarios y control de acceso por roles.

## Modelo de Usuario

### Backend: models/usuario.py
```python
from sqlalchemy import Column, String, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum

class RolUsuario(str, enum.Enum):
    administrador = "administrador"
    supervisor = "supervisor"
    operario = "operario"
    cliente = "cliente"

class Usuario(Base, BaseModel):
    __tablename__ = "usuarios"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    rol = Column(Enum(RolUsuario), nullable=False)
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    proyectos_creados = relationship("Proyecto", back_populates="creador")
    proyectos_asignados = relationship("Proyecto", back_populates="cliente")
```

### Schemas: schemas/usuario.py
```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.usuario import RolUsuario

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    rol: RolUsuario

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id: UUID
    activo: bool
    ultimo_acceso: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # user_id
    rol: RolUsuario
    exp: datetime
```

## Seguridad: core/security.py
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_password(password_plano: str, password_hash: str) -> bool:
    return pwd_context.verify(password_plano, password_hash)

def hashear_password(password: str) -> str:
    return pwd_context.hash(password)

def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def crear_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verificar_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

## Dependencias: core/deps.py
```python
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import verificar_token
from app.models.usuario import Usuario, RolUsuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_usuario_actual(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verificar_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == user_id, Usuario.activo == True).first()
    if usuario is None:
        raise credentials_exception

    return usuario

def require_roles(*roles: RolUsuario):
    async def role_checker(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para esta acción"
            )
        return usuario
    return role_checker

# Shortcuts
require_admin = require_roles(RolUsuario.administrador)
require_admin_or_supervisor = require_roles(RolUsuario.administrador, RolUsuario.supervisor)
require_staff = require_roles(RolUsuario.administrador, RolUsuario.supervisor, RolUsuario.operario)
```

## Endpoint: api/v1/endpoints/auth.py
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.deps import get_db, get_usuario_actual
from app.core.security import verificar_password, hashear_password, crear_access_token, crear_refresh_token
from app.schemas.usuario import Token, UsuarioResponse
from app.models.usuario import Usuario

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    usuario = db.query(Usuario).filter(
        Usuario.email == form_data.username,
        Usuario.activo == True
    ).first()

    if not usuario or not verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )

    # Actualizar último acceso
    usuario.ultimo_acceso = datetime.utcnow()
    db.commit()

    token_data = {"sub": str(usuario.id), "rol": usuario.rol.value}

    return Token(
        access_token=crear_access_token(token_data),
        refresh_token=crear_refresh_token(token_data)
    )

@router.get("/me", response_model=UsuarioResponse)
def get_current_user(usuario: Usuario = Depends(get_usuario_actual)):
    return usuario

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    from app.core.security import verificar_token

    payload = verificar_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(Usuario.id == payload["sub"]).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    token_data = {"sub": str(usuario.id), "rol": usuario.rol.value}

    return Token(
        access_token=crear_access_token(token_data),
        refresh_token=crear_refresh_token(token_data)
    )
```

## Frontend: stores/authStore.ts
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from '@/services/api';

interface Usuario {
  id: string;
  email: string;
  nombre: string;
  rol: 'administrador' | 'supervisor' | 'operario' | 'cliente';
}

interface AuthState {
  usuario: Usuario | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUsuario: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      usuario: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const formData = new FormData();
          formData.append('username', email);
          formData.append('password', password);

          const { data } = await api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });

          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);

          set({ accessToken: data.access_token, isAuthenticated: true });
          await get().fetchUsuario();
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ usuario: null, accessToken: null, isAuthenticated: false });
      },

      fetchUsuario: async () => {
        try {
          const { data } = await api.get('/auth/me');
          set({ usuario: data });
        } catch {
          get().logout();
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ accessToken: state.accessToken }),
    }
  )
);
```

## Frontend: pages/auth/Login.tsx
```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'Contraseña requerida'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function Login() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();
  const [error, setError] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      setError('');
      await login(data.email, data.password);
      navigate('/dashboard');
    } catch {
      setError('Email o contraseña incorrectos');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <img src="/logo.svg" alt="Electro América" className="h-16 mx-auto mb-4" />
          <h1 className="text-2xl font-bold">Iniciar Sesión</h1>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <div className="bg-primary-light text-primary-dark p-3 rounded-md text-sm">
                {error}
              </div>
            )}
            <div>
              <Input
                type="email"
                placeholder="Email"
                {...register('email')}
              />
              {errors.email && (
                <span className="text-primary text-sm">{errors.email.message}</span>
              )}
            </div>
            <div>
              <Input
                type="password"
                placeholder="Contraseña"
                {...register('password')}
              />
              {errors.password && (
                <span className="text-primary text-sm">{errors.password.message}</span>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Ingresando...' : 'Ingresar'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

## Checklist de Completado
- [ ] Modelo Usuario con roles
- [ ] Schemas Pydantic para auth
- [ ] Security utils (JWT, bcrypt)
- [ ] Dependencies con role checking
- [ ] Endpoints login, me, refresh
- [ ] Zustand auth store
- [ ] Login page con form
- [ ] Protected routes
- [ ] Middleware de roles en frontend
