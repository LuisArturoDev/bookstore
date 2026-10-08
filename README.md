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

La carga automática de archivos `.env` no está configurada; establece las variables necesarias en el entorno del proceso.

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
- [x] FASE 4 — Filtros.
- [x] FASE 5 — Integración de tasas de cambio.
- [x] FASE 6 — Cálculo del precio.
- [x] FASE 7 — Tests.
- [x] FASE 8 — Frontend.
- [ ] FASE 9 — Integración completa.
- [ ] FASE 10 — Colección Postman.
- [ ] FASE 11 — Documentación final.
- [ ] FASE 12 — Docker (opcional).

React y Vite están inicializados en FASE 8. La integración completa de todos los flujos se revisará en FASE 9.

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

### Filtros de inventario (FASE 4)

| Método | Ruta | Comportamiento |
|---|---|---|
| `GET` | `/books/search?category=Literature` | Filtra por categoría sin distinguir mayúsculas/minúsculas; elimina espacios al inicio/final del valor. |
| `GET` | `/books/low-stock?threshold=10` | Devuelve libros cuyo stock es menor o igual al umbral. El umbral predeterminado es 10. |

Ambos endpoints conservan la paginación de `/books`, incluyendo `page`, `page_size` y `count`/`next`/`previous`/`results`. Una categoría ausente o en blanco, o un umbral que no sea un entero no negativo, produce `400 Bad Request`. Un filtro válido sin coincidencias devuelve una página vacía con `200 OK`.

Para ejecutar las pruebas focalizadas de CRUD y filtros:

```powershell
python backend\manage.py test books.tests
```

### Servicio de tasa de cambio (FASE 5)

`books.services.exchange_rate_service.ExchangeRateService` consulta `EXCHANGE_RATE_API_URL` con un timeout configurable, extrae la tasa de `LOCAL_CURRENCY` y la devuelve como `Decimal`. Si la solicitud falla o la respuesta no incluye una tasa positiva válida, usa `DEFAULT_EXCHANGE_RATE` y marca `used_fallback=True`. Si también falta una tasa de fallback válida, lanza `ExchangeRateUnavailable` para que la capa de negocio decida cómo responder. El servicio no modifica libros y todavía no está conectado al cálculo ni a ningún endpoint.

Configurar `EXCHANGE_RATE_API_URL`, `LOCAL_CURRENCY`, `EXCHANGE_RATE_TIMEOUT` (entero positivo) y `DEFAULT_EXCHANGE_RATE` como variables de entorno del proceso. `.env.example` documenta los nombres, pero Django aún no carga automáticamente archivos `.env`. La tasa `0.85` es ilustrativa, no una cotización vigente.

Las pruebas del servicio simulan respuestas, errores HTTP y timeouts; no requieren conexión con el proveedor:

```powershell
python backend\manage.py test books.tests.ExchangeRateServiceTests
```

### Cálculo del precio (FASE 6)

`PriceCalculationService` combina el costo en USD con la tasa recibida de `ExchangeRateService`, aplica un margen del 40% y persiste `selling_price_local`. Conserva `Decimal` y precisión intermedia durante la operación; redondea el costo local mostrado y el precio final con `ROUND_HALF_UP` a dos decimales.

El endpoint `POST /books/{id}/calculate-price` devuelve `book_id`, costo USD, tasa, costo local, margen, precio sugerido, moneda, `used_fallback` y timestamp UTC. Si el libro no existe, responde `404`. Si ni la API externa ni el fallback ofrecen una tasa válida, responde `503` y no actualiza el precio. La vista delega el cálculo al servicio; el servicio recibe la dependencia de tasa y es comprobable sin llamadas HTTP reales.

Para ejecutar las pruebas del cálculo:

```powershell
python backend\manage.py test books.tests.PriceCalculationTests
```

### Aplicación frontend (FASE 8)

En una terminal, inicia el backend:

```powershell
python backend\manage.py runserver
```

En otra terminal, inicia React/Vite:

```powershell
cd frontend
npm install
npm run dev
```

Abre la URL indicada por Vite (por defecto `http://localhost:5173`). El proxy de desarrollo reenvía `/books` y `/health` a Django en `http://127.0.0.1:8000`; esto evita instalar y configurar CORS solo para desarrollo local. La SPA permite listar y paginar, filtrar por categoría/stock bajo, crear, editar, eliminar con confirmación y calcular el precio sugerido.

Verificar frontend:

```powershell
cd frontend
npm run lint
npm run build
```

Consulta [frontend/README.md](./frontend/README.md) para instrucciones y detalles del proxy.

### Suite de pruebas backend (FASE 7)

La suite cubre validación del modelo/serializer, CRUD, filtros, paginación, servicio de tasas y cálculo del precio, incluidos los principales errores esperados. Las respuestas y fallos del proveedor externo se simulan, por lo que los tests no necesitan acceso a Internet.

Desde la raíz del repositorio, ejecuta todas las pruebas backend con:

```powershell
python backend\manage.py test books.tests
```

## Contexto de la prueba

El alcance y las reglas de implementación están descritos en [Nextep_Prueba_Tecnica_Contexto_Copilot.md](./Nextep_Prueba_Tecnica_Contexto_Copilot.md).
