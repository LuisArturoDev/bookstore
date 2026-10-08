# Bookstore Inventory

Aplicación Full Stack para administrar el inventario de una librería. Este repositorio corresponde a una prueba técnica y se desarrollará de forma incremental para que cada parte pueda explicarse y verificarse antes de avanzar.

## Stack previsto

- **Backend:** Python, Django y Django REST Framework.
- **Frontend:** React con Vite y JavaScript.
- **Base de datos:** SQLite para el desarrollo inicial; la configuración se concretará en la fase del backend.
- **Integración posterior:** API de tasas de cambio para calcular el precio de venta sugerido.

Se eligen React/Vite y JavaScript por ser la opción preferida en el contexto del proyecto y mantener simple el frontend inicial. SQLite permite comenzar el desarrollo local sin levantar un servicio adicional. Estas decisiones no impiden cambiar de base de datos si los requisitos de despliegue lo justifican.

## Estructura prevista

```text
.
├── backend/     # Proyecto Django y API
├── frontend/    # Aplicación React/Vite
├── .env.example # Plantilla de configuración local
└── README.md
```

Los directorios `backend/` y `frontend/` se crearán en sus fases respectivas; todavía no contienen aplicaciones en esta fase de preparación.

## Configuración local

1. Copiar `.env.example` a `.env`.
2. Reemplazar `SECRET_KEY` por un secreto local. No subir `.env` al repositorio.
3. Mantener `LOCAL_CURRENCY=EUR` como moneda inicial del ejemplo, salvo que se acuerde otra.
4. `DEFAULT_EXCHANGE_RATE=0.85` es un valor ilustrativo para el fallback, no una cotización vigente. Debe corresponder a `LOCAL_CURRENCY`.

La integración de tasas y la lectura de estas variables se implementarán en fases posteriores.

## Estado del desarrollo

- [x] FASE 0 — Preparación del repositorio y configuración inicial.
- [ ] FASE 1 — Django básico.
- [ ] FASE 2 — Modelo `Book`.
- [ ] FASE 3 — CRUD.
- [ ] FASE 4 — Filtros.
- [ ] FASE 5 — Integración de tasas de cambio.
- [ ] FASE 6 — Cálculo del precio.
- [ ] FASE 7 — Tests.
- [ ] FASE 8 — Frontend.
- [ ] FASE 9 — Integración completa.
- [ ] FASE 10 — Colección Postman.
- [ ] FASE 11 — Documentación final.
- [ ] FASE 12 — Docker (opcional).

En esta fase no se han inicializado Django, DRF, React ni Vite. Las instrucciones para ejecutar backend y frontend se agregarán cuando esas aplicaciones existan.

## Contexto de la prueba

El alcance y las reglas de implementación están descritos en [Nextep_Prueba_Tecnica_Contexto_Copilot.md](./Nextep_Prueba_Tecnica_Contexto_Copilot.md).
