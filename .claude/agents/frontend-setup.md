# Agente: Frontend Setup

## Rol
Configuración inicial del frontend con React 18, TypeScript, Vite, Tailwind CSS y shadcn/ui.

## Identidad Visual Electro América

### Colores
```css
:root {
  --ea-red: #E53935;
  --ea-red-dark: #C62828;
  --ea-red-light: #FFEBEE;
  --ea-black: #1A1A1A;
  --ea-gray-dark: #424242;
  --ea-gray: #757575;
  --ea-gray-light: #F5F5F5;
  --ea-white: #FFFFFF;
}
```

### Tailwind Config
```javascript
colors: {
  primary: {
    DEFAULT: '#E53935',
    dark: '#C62828',
    light: '#FFEBEE',
  },
  neutral: {
    900: '#1A1A1A',
    700: '#424242',
    500: '#757575',
    100: '#F5F5F5',
  }
}
```

## Estructura de Carpetas
```
frontend/
├── public/
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── AdminLayout.tsx
│   │   │   └── ClientLayout.tsx
│   │   └── shared/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── ConfirmDialog.tsx
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── Login.tsx
│   │   │   └── index.ts
│   │   ├── dashboard/
│   │   ├── proyectos/
│   │   ├── materiales/
│   │   ├── equipos/
│   │   ├── gastos/
│   │   ├── finanzas/
│   │   ├── reportes/
│   │   ├── usuarios/
│   │   └── portal-cliente/
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useProyectos.ts
│   │   └── index.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   └── index.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   └── index.ts
│   ├── types/
│   │   ├── auth.ts
│   │   ├── proyecto.ts
│   │   └── index.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── vite.config.ts
└── Dockerfile
```

## Dependencias (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.14.0",
    "@tanstack/react-table": "^8.11.0",
    "zustand": "^4.4.7",
    "react-hook-form": "^7.49.0",
    "@hookform/resolvers": "^3.3.2",
    "zod": "^3.22.4",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "date-fns": "^3.0.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.2.0",
    "lucide-react": "^0.300.0",
    "class-variance-authority": "^0.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0"
  }
}
```

## Archivos Base

### tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#E53935',
          dark: '#C62828',
          light: '#FFEBEE',
          foreground: '#FFFFFF',
        },
        background: '#F5F5F5',
        foreground: '#1A1A1A',
        muted: {
          DEFAULT: '#757575',
          foreground: '#424242',
        },
        border: '#E0E0E0',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### src/utils/formatters.ts
```typescript
export const formatearMonto = (monto: number): string => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(monto);
};

export const formatearFecha = (fecha: Date | string): string => {
  const date = typeof fecha === 'string' ? new Date(fecha) : fecha;
  return new Intl.DateTimeFormat('es-AR').format(date);
};

export const formatearPorcentaje = (valor: number): string => {
  return `${Math.round(valor)}%`;
};
```

### src/services/api.ts
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

## Comandos de Inicialización
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npx shadcn-ui@latest init
npm run dev
```

## shadcn/ui Components a Instalar
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add form
npx shadcn-ui@latest add select
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add progress
```

## Checklist de Completado
- [ ] Vite + React + TypeScript inicializado
- [ ] Tailwind CSS configurado con colores EA
- [ ] shadcn/ui instalado y configurado
- [ ] Estructura de carpetas creada
- [ ] Axios configurado con interceptors
- [ ] React Router configurado
- [ ] Zustand store base
- [ ] TanStack Query provider
- [ ] Layouts admin y cliente separados
