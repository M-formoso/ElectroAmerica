# Deploy en Railway - Electro América

## Estructura del Proyecto

El proyecto tiene 2 servicios para deployar:
- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React (Vite) + Nginx

---

## Paso 1: Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app) e inicia sesión
2. Click en **"New Project"**
3. Selecciona **"Empty Project"**

---

## Paso 2: Agregar PostgreSQL

1. En tu proyecto, click en **"+ New"**
2. Selecciona **"Database"** → **"Add PostgreSQL"**
3. Railway creará automáticamente la variable `DATABASE_URL`

---

## Paso 3: Deploy del Backend

### Opción A: Desde GitHub (Recomendado)

1. Click en **"+ New"** → **"GitHub Repo"**
2. Selecciona tu repositorio
3. En **"Settings"**, configura:
   - **Root Directory**: `backend`
   - **Build Command**: (dejar vacío, usa Dockerfile)

### Opción B: Usando Railway CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Ir a la carpeta backend
cd backend

# Iniciar deploy
railway up
```

### Variables de Entorno del Backend

En Railway, ve a tu servicio backend → **Variables** y agrega:

```env
# Obligatorias
SECRET_KEY=tu-clave-secreta-muy-larga-y-segura-minimo-32-caracteres
ENVIRONMENT=production
DEBUG=false

# CORS (agregar URL del frontend cuando lo tengas)
CORS_ORIGINS=https://tu-frontend.up.railway.app

# Cloudinary (para subir fotos)
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret

# Usuario admin inicial (opcional, cambiar después)
FIRST_SUPERUSER_EMAIL=admin@electroamerica.com
FIRST_SUPERUSER_PASSWORD=CambiarEstaPassword123!
```

> **IMPORTANTE**: La variable `DATABASE_URL` se conecta automáticamente si agregaste PostgreSQL al mismo proyecto.

---

## Paso 4: Deploy del Frontend

1. Click en **"+ New"** → **"GitHub Repo"**
2. Selecciona tu repositorio
3. En **"Settings"**, configura:
   - **Root Directory**: `frontend`
   - **Build Command**: (dejar vacío, usa Dockerfile)

### Variables de Entorno del Frontend

```env
VITE_API_URL=https://tu-backend.up.railway.app/api/v1
```

---

## Paso 5: Configurar Dominios

### Backend
1. Ve al servicio backend → **Settings** → **Networking**
2. Click en **"Generate Domain"**
3. Copia la URL (ej: `backend-production-xxxx.up.railway.app`)

### Frontend
1. Ve al servicio frontend → **Settings** → **Networking**
2. Click en **"Generate Domain"**
3. Copia la URL

### Actualizar CORS
Después de tener el dominio del frontend, actualiza la variable `CORS_ORIGINS` del backend.

---

## Paso 6: Verificar Deploy

1. **Backend**: Visita `https://tu-backend.up.railway.app/health`
   - Debería mostrar: `{"status": "healthy", ...}`

2. **Frontend**: Visita `https://tu-frontend.up.railway.app`
   - Debería mostrar la página de login

3. **Login**:
   - Email: `admin@electroamerica.com`
   - Password: El que configuraste en `FIRST_SUPERUSER_PASSWORD`

---

## Opcional: Agregar Redis (para Celery)

Si necesitas tareas en background:

1. Click en **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway conectará automáticamente `REDIS_URL`

---

## Costos Estimados

Railway ofrece $5 USD gratis al mes. Estimación:

| Servicio | Costo/mes |
|----------|-----------|
| PostgreSQL | ~$5 |
| Backend | ~$5-10 |
| Frontend | ~$3-5 |
| Redis (opcional) | ~$5 |

**Total**: ~$13-20 USD/mes (sin Redis)

---

## Troubleshooting

### Error de conexión a BD
- Verificar que PostgreSQL esté en el mismo proyecto
- La variable `DATABASE_URL` debe conectarse automáticamente

### Error CORS
- Agregar la URL exacta del frontend a `CORS_ORIGINS`
- Incluir `https://` en la URL

### Migraciones no corren
- Verificar los logs del backend
- El Procfile debería ejecutar `alembic upgrade head` automáticamente

### Frontend no encuentra API
- Verificar `VITE_API_URL` está configurada correctamente
- Debe incluir `/api/v1` al final

---

## Dominio Personalizado

1. Ve a **Settings** → **Networking** → **Custom Domain**
2. Agrega tu dominio (ej: `api.electroamerica.com`)
3. Configura los DNS según las instrucciones de Railway

---

## Comandos Útiles

```bash
# Ver logs
railway logs

# Abrir consola
railway shell

# Ejecutar comando
railway run alembic upgrade head

# Ver variables
railway variables
```
