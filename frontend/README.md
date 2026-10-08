# Bookwise frontend

SPA de inventario construida con React y Vite. Consume la API Django mediante rutas relativas (`/books`, `/books/search`, `/books/low-stock`); el servidor de desarrollo de Vite las reenvía a `http://127.0.0.1:8000`, evitando configuración CORS adicional durante el desarrollo local.

## Requisitos y ejecución

Requiere Node.js y npm.

1. Inicia Django desde la raíz del repositorio:

   ```powershell
   python backend\manage.py runserver
   ```

2. En otra terminal inicia la SPA:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

3. Abre la dirección que Vite muestra (normalmente `http://localhost:5173`).

La API debe estar disponible en `http://127.0.0.1:8000`. La configuración del proxy de desarrollo está en `vite.config.js`.

## Funcionalidades

- Dashboard paginado.
- Filtro por categoría y vista de stock bajo.
- Alta, edición con `PUT` y eliminación confirmada.
- Cálculo del precio sugerido, incluyendo tasa usada y si se aplicó fallback.
- Estados de carga, vacíos, errores y notificaciones.

Validar calidad y compilación:

```powershell
npm run lint
npm run build
```

El build de Vite es una salida estática. Su integración con un servidor de producción se definirá en una fase posterior.
