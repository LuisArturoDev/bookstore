# Bookstore Inventory

Aplicación Full Stack para administrar el inventario de una librería. Este repositorio corresponde a una prueba técnica y se desarrollará de forma incremental para que cada parte pueda explicarse y verificarse antes de avanzar.

## Stack previsto

- **Backend:** Python, Django y Django REST Framework.
- **Frontend:** React con Vite y JavaScript.
- **Base de datos:** SQLite para el desarrollo local (configurada en FASE 1).
- **Integración posterior:** API de tasas de cambio para calcular el precio de venta sugerido.

Se eligen React/Vite y JavaScript por ser la opción preferida en el contexto del proyecto y mantener simple el frontend inicial. SQLite permite comenzar el desarrollo local sin levantar un servicio adicional. Estas decisiones no impiden cambiar de base de datos si los requisitos de despliegue lo justifican.

## Estructura prevista

```text
.
├── backend/     # Proyecto Django y API (FASE 1)
├── frontend/    # Aplicación React/Vite
├── .env.example # Plantilla de configuración local
└── README.md
```

El proyecto Django ya está inicializado dentro de `backend/`. El directorio `frontend/` se creará en FASE 8.

## Configuración local

1. `.env.example` documenta las variables previstas; Django todavía no carga archivos `.env` automáticamente.
2. Para esta fase, el backend usa valores predeterminados de desarrollo. No utilizar esos valores en producción.
3. Antes de desplegar, configurar `SECRET_KEY` en el entorno del proceso y `DEBUG=False`. No subir secretos al repositorio.
4. `LOCAL_CURRENCY=EUR` y `DEFAULT_EXCHANGE_RATE=0.85` se usarán en las fases de cálculo. La tasa es ilustrativa, no una cotización vigente, y debe corresponder a `LOCAL_CURRENCY`.

La integración de tasas y la lectura de estas variables se implementarán en fases posteriores.

## Backend: instalación local

Requisitos: Python 3.10 o posterior compatible con la versión de Django instalada.

Desde la raíz del repositorio, en PowerShell:

```powershell
py -3 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python backend\manage.py makemigrations books
python backend\manage.py migrate
python backend\manage.py runserver
```

Comprobar que Django responde visitando `http://127.0.0.1:8000/health/`; debe devolver `{"status":"ok"}`.

La base local SQLite se crea al ejecutar las migraciones. El endpoint `/health/` solo verifica que la aplicación está activa; no es un endpoint de inventario.

Django lee `SECRET_KEY`, `DEBUG` y `ALLOWED_HOSTS` desde variables de entorno del proceso. Django no carga archivos `.env` por sí solo; en esta fase no se añadió una dependencia para hacerlo. El valor predeterminado de `SECRET_KEY` es únicamente para desarrollo local y no es seguro para producción. Al desactivar `DEBUG`, el backend exige que `SECRET_KEY` esté configurada.

## Estado del desarrollo

- [x] FASE 0 — Preparación del repositorio y configuración inicial.
- [x] FASE 1 — Django básico.
- [x] FASE 2 — Modelo `Book`.
- [x] FASE 3 — CRUD.
- [ ] FASE 4 — Filtros.
- [ ] FASE 5 — Integración de tasas de cambio.
- [ ] FASE 6 — Cálculo del precio.
- [ ] FASE 7 — Tests.
- [ ] FASE 8 — Frontend.
- [ ] FASE 9 — Integración completa.
- [ ] FASE 10 — Colección Postman.
- [ ] FASE 11 — Documentación final.
- [ ] FASE 12 — Docker (opcional).

React y Vite se inicializarán en FASE 8. Los filtros, las tasas de cambio y el cálculo de precio pertenecen a fases posteriores.

### Modelo `Book` (FASE 2)

El modelo persistente contiene los datos del libro, valida y normaliza ISBN-10/ISBN-13, impide ISBN duplicados y aplica restricciones de costo positivo y stock no negativo. `selling_price_local` permanece nulo hasta una fase posterior. Para ejecutar las pruebas del modelo y su serializer:

```powershell
python backend\manage.py test books.tests
```

### API CRUD de libros (FASE 3)

Con el servidor iniciado, la API expone estas rutas sin prefijo `/api` ni barra final:

| Método | Ruta | Resultado |
|---|---|---|
| `POST` | `/books` | Crea un libro y devuelve `201 Created`. |
| `GET` | `/books` | Devuelve la página solicitada. |
| `GET` | `/books/{id}` | Devuelve un libro o `404 Not Found`. |
| `PUT` | `/books/{id}` | Reemplaza los campos editables o devuelve `400`/`404`. |
| `DELETE` | `/books/{id}` | Elimina el libro y devuelve `204 No Content` o `404`. |

Ejemplo de creación:

```json
{
  "title": "The Example Book",
  "author": "Example Author",
  "isbn": "978-0-306-40615-7",
  "cost_usd": "15.99",
  "stock_quantity": 25,
  "category": "Fiction",
  "supplier_country": "US"
}
```

El listado usa paginación por número de página: `GET /books?page=2&page_size=20`. El tamaño predeterminado es 10 y el máximo es 100. La respuesta incluye `count`, `next`, `previous` y `results`. Los errores de entrada, incluido un ISBN inválido o duplicado, se devuelven como `400 Bad Request`. El precio sugerido y los timestamps son campos de solo lectura. `PUT` requiere todos los campos editables; no se habilitó `PATCH`.

Para ejecutar las pruebas del modelo, serializer y CRUD:

```powershell
python backend\manage.py test books.tests
```

## Contexto de la prueba

El alcance y las reglas de implementación están descritos en [Nextep_Prueba_Tecnica_Contexto_Copilot.md](./Nextep_Prueba_Tecnica_Contexto_Copilot.md).
