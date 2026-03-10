# /frontend - Operaciones Frontend

Ejecuta operaciones comunes del frontend.

## Argumentos:
- `run` - Ejecutar servidor de desarrollo
- `build` - Build de producción
- `lint` - Ejecutar linter
- `add` - Agregar componente shadcn/ui

## Comandos:

### Ejecutar desarrollo
```bash
cd frontend
npm run dev
```

### Build producción
```bash
cd frontend
npm run build
npm run preview
```

### Agregar componente shadcn/ui
```bash
cd frontend
npx shadcn-ui@latest add [componente]
```

Componentes comunes:
- `button`, `input`, `card`, `table`
- `dialog`, `dropdown-menu`, `form`
- `select`, `toast`, `tabs`, `badge`
- `avatar`, `progress`, `skeleton`

### Ejecutar linter
```bash
cd frontend
npm run lint
```

## Estructura esperada:
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/          # shadcn/ui
│   │   ├── layout/      # Header, Sidebar
│   │   └── shared/      # Componentes compartidos
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   ├── stores/
│   ├── types/
│   └── utils/
└── package.json
```

## Colores Tailwind (Electro América):
```javascript
colors: {
  primary: {
    DEFAULT: '#E53935',
    dark: '#C62828',
    light: '#FFEBEE',
  }
}
```

---
*Referencia: `.claude/agents/frontend-setup.md`*
