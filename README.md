# Bookstore Inventory

Aplicación Full Stack para gestionar el inventario de una librería. El backend expone una API REST con Django REST Framework; el frontend es una SPA en React/Vite. SQLite es la base de datos de desarrollo local.

## Requisitos

- Python 3.10 o posterior.
- Node.js `^20.19.0` o `>=22.12.0` y npm (requisitos de Vite 8).
- Git para clonar el repositorio.
- Postman, opcional, para usar la colección incluida.
- Docker no es necesario para el desarrollo y no forma parte de las fases completadas.

## Puesta en marcha local

Clona el repositorio y, desde su carpeta raíz, instala y ejecuta el backend en PowerShell:

```powershell
py -3 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python backend\manage.py migrate
python backend\manage.py runserver
```

Las migraciones versionadas crean la base SQLite en `backend\db.sqlite3`. No hace falta generar migraciones para iniciar el proyecto. Comprueba que el servidor responde en `http://127.0.0.1:8000/health/`; la respuesta esperada es:

```json
{
  "status": "ok"
}
```

En una segunda terminal, desde la raíz del repositorio, instala y ejecuta el frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Abre la dirección indicada por Vite, normalmente `http://localhost:5173`. El proxy configurado en `frontend/vite.config.js` reenvía `/books` y `/health` a Django en `http://127.0.0.1:8000`; no se requiere configuración CORS para este modo local.

## Configuración

Las variables reconocidas están listadas en [.env.example](./.env.example). Django **no carga automáticamente archivos `.env`** en este proyecto: establece las variables en el entorno del proceso antes de iniciar Django. Desde PowerShell, por ejemplo:

```powershell
$env:DEBUG = "True"
$env:SECRET_KEY = "reemplaza-por-un-secreto-local"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"
$env:EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
$env:LOCAL_CURRENCY = "EUR"
$env:EXCHANGE_RATE_TIMEOUT = "5"
$env:DEFAULT_EXCHANGE_RATE = "0.85"
python backend\manage.py runserver
```

Estas variables solo duran mientras viva esa sesión de PowerShell. La configuración predeterminada permite desarrollo local, pero la `SECRET_KEY` de desarrollo no es segura para producción. Con `DEBUG=False`, configura explícitamente `SECRET_KEY`; configura también `ALLOWED_HOSTS` para los hosts reales.

| Variable | Predeterminado | Uso |
|---|---|---|
| `DEBUG` | `True` | Modo de depuración Django. |
| `SECRET_KEY` | Clave insegura solo para desarrollo local | Clave criptográfica Django; obligatoria cuando `DEBUG=False`. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Lista separada por comas de hosts permitidos. |
| `EXCHANGE_RATE_API_URL` | `https://api.exchangerate-api.com/v4/latest/USD` | Endpoint externo que devuelve tasas bajo el objeto `rates`. |
| `LOCAL_CURRENCY` | `EUR` | Código de moneda local de tres letras; se usa la tasa de esa moneda respecto a USD. |
| `EXCHANGE_RATE_TIMEOUT` | `5` | Timeout de la petición externa, en segundos; debe ser entero positivo. |
| `DEFAULT_EXCHANGE_RATE` | `0.85` | Tasa de respaldo positiva. El valor incluido es ilustrativo, no una cotización actual, y debe corresponder a `LOCAL_CURRENCY`. |

## Funcionalidad

- Alta, consulta, edición completa (`PUT`) y eliminación de libros.
- Validación de ISBN-10/ISBN-13, normalización y unicidad.
- Búsqueda por categoría y filtro de existencias bajas.
- Paginación del listado.
- Cálculo y persistencia del precio sugerido, con margen del 40%.
- Consulta de tasa externa con fallback configurado.
- Dashboard React para las operaciones, estados de carga y mensajes de error.

Los importes se manejan en el backend como decimales y el precio calculado se redondea a dos decimales con `ROUND_HALF_UP`. El precio local guardado debe interpretarse junto con la moneda configurada en `LOCAL_CURRENCY`.

## API

La API usa las rutas exactas siguientes: no tienen prefijo `/api` ni barra final, salvo `/health/`.

| Método | Ruta | Descripción | Respuestas principales |
|---|---|---|---|
| `GET` | `/health/` | Comprueba que Django responde. | `200` |
| `POST` | `/books` | Crea un libro. | `201`, `400` |
| `GET` | `/books` | Lista libros paginados. | `200` |
| `GET` | `/books/{id}` | Obtiene un libro. | `200`, `404` |
| `PUT` | `/books/{id}` | Reemplaza todos los campos editables. | `200`, `400`, `404` |
| `DELETE` | `/books/{id}` | Elimina un libro. | `204`, `404` |
| `GET` | `/books/search?category=Fiction` | Filtra por categoría, sin distinguir mayúsculas/minúsculas. | `200`, `400` |
| `GET` | `/books/low-stock?threshold=10` | Devuelve libros con stock menor o igual al umbral. | `200`, `400` |
| `POST` | `/books/{id}/calculate-price` | Calcula y guarda el precio sugerido. | `200`, `404`, `503` |

Los endpoints de listado y filtros aceptan `page` y `page_size`. El tamaño predeterminado es 10 y el máximo, 100. Devuelven `count`, `next`, `previous` y `results`. Los errores de validación usan `400`; los filtros sin coincidencias devuelven `200` con resultados vacíos. No está habilitado `PATCH`.

### Crear un libro

Petición `POST /books` con `Content-Type: application/json`:

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

`cost_usd` debe ser mayor que cero y tener como máximo dos decimales; `stock_quantity` debe ser un entero no negativo; `supplier_country` debe ser un código de dos letras en mayúsculas. El ISBN se normaliza y debe ser válido y único. El precio sugerido y los timestamps son de solo lectura.

### Calcular el precio sugerido

Envía `POST /books/{id}/calculate-price` con un cuerpo JSON vacío (`{}`). El backend usa la tasa externa; ante un fallo o respuesta inválida, usa `DEFAULT_EXCHANGE_RATE`. Un cálculo correcto devuelve, entre otros campos:

```json
{
  "book_id": 1,
  "cost_usd": 15.99,
  "exchange_rate": 0.85,
  "cost_local": 13.59,
  "margin_percentage": 40,
  "selling_price_local": 19.03,
  "currency": "EUR",
  "used_fallback": false,
  "calculation_timestamp": "2026-10-08T20:00:00Z"
}
```

Los valores numéricos de la respuesta dependen de la tasa obtenida. `used_fallback` indica si se usó la tasa de respaldo. Si no hay una tasa externa válida ni un fallback válido, responde `503` y no guarda un nuevo precio; un ID inexistente responde `404`.

## Pruebas y validación

Desde la raíz, activa el entorno virtual del backend y ejecuta la suite:

```powershell
backend\.venv\Scripts\Activate.ps1
python backend\manage.py test books.tests
```

La suite cubre modelo, serializer, CRUD, filtros, paginación, tasa de cambio y cálculo. Las llamadas externas se simulan, así que los tests no requieren acceso al proveedor de tasas.

Para verificar frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Postman

Importa [la colección Bookstore Inventory API](./postman/Bookstore%20Inventory%20API.postman_collection.json) en Postman. Inicia Django y deja `base_url` en `http://127.0.0.1:8000` o cámbiala según tu entorno. Ejecuta `Create Book` primero; las demás solicitudes usan el ID creado. Ejecuta `Delete Book` al terminar para limpiar el libro de prueba.

## Estructura del repositorio

```text
backend/       Proyecto Django, API, modelo y tests
frontend/      SPA React/Vite
postman/       Colección Postman de la API
.env.example   Referencia de variables de configuración
```

## Estado del desarrollo

- [x] FASE 0 — Preparación del repositorio.
- [x] FASE 1 — Django básico.
- [x] FASE 2 — Modelo `Book`.
- [x] FASE 3 — CRUD.
- [x] FASE 4 — Filtros.
- [x] FASE 5 — Servicio de tasa de cambio.
- [x] FASE 6 — Cálculo del precio.
- [x] FASE 7 — Tests backend.
- [x] FASE 8 — Frontend.
- [x] FASE 9 — Integración completa.
- [x] FASE 10 — Colección Postman.
- [x] FASE 11 — Documentación final.
- [ ] FASE 12 — Docker (opcional, no implementado).

Las reglas y el contexto ampliado de la prueba están en [Nextep_Prueba_Tecnica_Contexto_Copilot.md](./Nextep_Prueba_Tecnica_Contexto_Copilot.md).
