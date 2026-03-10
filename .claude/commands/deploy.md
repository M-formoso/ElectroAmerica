# /deploy - Preparar Deploy

Prepara el proyecto para deploy en producción.

## Pre-deploy checklist:

### 1. Verificar configuración
- [ ] Variables de entorno configuradas
- [ ] SECRET_KEY segura
- [ ] DATABASE_URL de producción
- [ ] CLOUDINARY configurado
- [ ] CORS origins configurados

### 2. Build del frontend
```bash
cd frontend
npm run build
```

### 3. Tests
```bash
cd backend
pytest -v
cd ../frontend
npm run test
```

### 4. Migraciones
```bash
cd backend
alembic upgrade head
```

## Docker Compose (Producción)

### docker-compose.prod.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: electro_america
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: always

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app worker --loglevel=info
    depends_on:
      - redis
      - backend
    restart: always

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app beat --loglevel=info
    depends_on:
      - redis
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./certbot/conf:/etc/letsencrypt
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
```

## Variables de entorno (producción)
```bash
# .env.production
DATABASE_URL=postgresql://user:password@postgres:5432/electro_america
SECRET_KEY=your-super-secret-production-key
REDIS_URL=redis://redis:6379/0
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=your-key
CLOUDINARY_API_SECRET=your-secret
VITE_API_URL=https://api.electroamerica.com/api/v1
```

## Deploy en VPS

### 1. Clonar repositorio
```bash
git clone https://github.com/your-repo/electro-america.git
cd electro-america
```

### 2. Configurar variables
```bash
cp .env.example .env.production
nano .env.production
```

### 3. Build y ejecutar
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. Verificar
```bash
curl https://api.electroamerica.com/health
```

## Backup de base de datos
```bash
docker-compose exec postgres pg_dump -U user electro_america > backup_$(date +%Y%m%d).sql
```

---
*Referencia: `.claude/CLAUDE.md` para configuración completa*
