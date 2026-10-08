# Bookstore Inventory

Aplicación Full Stack para gestionar el inventario de una librería. El backend expone una API REST con Django REST Framework; el frontend es una SPA en React/Vite. SQLite es la base de datos de desarrollo local.

## Requisitos

- Python 3.10 o posterior.
- Node.js `^20.19.0` o `>=22.12.0` y npm (requisitos de Vite 8).
- Git para clonar el repositorio.
- Postman, opcional, para usar la colección incluida.
- Docker Engine y Docker Compose v2, opcionales para iniciar el stack en contenedores.

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

Como alternativa, puedes ejecutar el stack con Docker Compose siguiendo la sección [Docker](#docker-fase-12-opcional).

## Configuración

Las variables reconocidas por Django están listadas en [.env.example](./.env.example). Django **no carga automáticamente archivos `.env`** al ejecutarse directamente: establece las variables en el entorno del proceso antes de iniciar Django. Desde PowerShell, por ejemplo:

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
| `APP_PORT` | `8080` | Puerto del host publicado por Docker Compose para el frontend; no lo utiliza Django. |

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

La API usa las rutas exactas siguientes: no tienen prefijo `/api` ni barra final, salvo el endpoint de salud, disponible como `/health` y `/health/`.

| Método | Ruta | Descripción | Respuestas principales |
|---|---|---|---|
| `GET` | `/health` o `/health/` | Comprueba que Django responde; es para monitoreo, no una página de navegación. | `200` |
| `POST` | `/books` | Crea un libro. | `201`, `400` |
| `GET` | `/books` | Lista libros paginados. | `200` |
| `GET` | `/books/{id}` | Obtiene un libro. | `200`, `404` |
| `PUT` | `/books/{id}` | Reemplaza todos los campos editables. | `200`, `400`, `404` |
| `DELETE` | `/books/{id}` | Elimina un libro. | `204`, `404` |
| `GET` | `/books/search?title=great&category=Fiction` | Filtra por texto parcial del título, categoría o ambos. | `200`, `400` |
| `GET` | `/books/low-stock?threshold=10` | Devuelve libros con stock menor o igual al umbral. | `200`, `400` |
| `POST` | `/books/{id}/calculate-price` | Calcula y guarda el precio sugerido. | `200`, `404`, `503` |

Los endpoints de listado y filtros aceptan `page` y `page_size`. El tamaño predeterminado es 10 y el máximo, 100. Devuelven `count`, `next`, `previous` y `results`, ordenados por ID descendente para mostrar primero el libro más reciente. La búsqueda usa el parámetro opcional `title` para coincidencia parcial, sin distinguir mayúsculas/minúsculas; `category` filtra por categoría, también sin distinguir mayúsculas/minúsculas. Se puede enviar uno o ambos, y ambos se combinan con AND. Si no se proporciona ninguno, responde `400`. Los errores de validación usan `400`; los filtros válidos sin coincidencias devuelven `200` con resultados vacíos. No está habilitado `PATCH`.

Ejemplos de búsqueda:

```text
GET /books/search?title=harry
GET /books/search?category=Fantasy
GET /books/search?title=harry&category=Fantasy
```

La interfaz permite buscar por nombre del libro (título), categoría o ambos criterios; el filtro de existencias bajas se mantiene independiente.

### Cargar libros de demostración

El catálogo local `backend/books/data/demo_books.json` contiene 200 títulos reales con autor e ISBN-13 obtenidos de [Open Library](https://openlibrary.org/). No incluye portadas; los libros sin imagen muestran las iniciales del título. Para agregarlos al inventario de desarrollo:

```powershell
python backend\manage.py seed_demo_books
```

En Docker Compose:

```powershell
docker compose exec backend python manage.py seed_demo_books
```

El comando es idempotente: omite los ISBN que ya existan y no modifica ni elimina libros guardados. Se puede volver a ejecutar sin duplicar el catálogo. Una migración elimina el antiguo registro de prueba independiente de Harry Potter (ISBN `9782123456803`) para dejar únicamente los 200 registros del catálogo dummy.

El inventario se puede visualizar como tabla o como tarjetas desde el selector junto a los resultados. Ambas vistas conservan acciones, filtros y paginación, y muestran skeletons mientras se cargan los libros.

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

El título admite hasta 150 caracteres, el autor hasta 100 y la categoría hasta 50; estos límites se aplican tanto en el formulario como en la API para evitar registros excesivamente largos. `cost_usd` debe ser mayor que cero y tener como máximo dos decimales; `stock_quantity` debe ser un entero no negativo; `supplier_country` debe ser un código de dos letras en mayúsculas. El ISBN se normaliza y debe ser válido y único. La portada `image` es opcional; admite JPG, PNG o WebP hasta 5 MB. Para cargar archivos, envía la creación o actualización como `multipart/form-data`; sin imagen se puede seguir usando JSON. Al actualizar, `remove_image=true` quita una portada existente si no se envía una nueva imagen. Los archivos reemplazados, quitados o asociados a un libro eliminado se limpian después de confirmar la transacción. El precio sugerido y los timestamps son de solo lectura.

El inventario muestra tarjetas por defecto y permite alternar a la tabla; la vista elegida se guarda en `localStorage` para conservar la preferencia en futuras visitas. También permite alternar entre tema claro y oscuro, guardando la elección localmente. La interfaz usa iconos SVG consistentes. Ambas vistas incluyen portada si existe; si no, presentan las iniciales del título. El título se muestra completo y al seleccionar una tarjeta o fila se abre el detalle del libro.

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

Importa [la colección Bookstore Inventory API](./postman/Bookstore%20Inventory%20API.postman_collection.json), ubicada en `postman/Bookstore Inventory API.postman_collection.json`, en Postman. Incluye todas las rutas: Health Check; crear, listar, consultar, actualizar y eliminar libros; buscar por título/categoría; filtrar por stock bajo; y calcular el precio. Con Django local, configura `base_url` como `http://127.0.0.1:8000`; con Docker, usa `http://127.0.0.1:8080` para pasar por el proxy Nginx. Ejecuta `Create Book` primero; las demás solicitudes de libro usan el ID creado. Ejecuta `Delete Book` al terminar para limpiar el libro de prueba.

## Docker (FASE 12, opcional)

Requiere Docker Engine y Docker Compose v2. Desde la raíz del repositorio, crea un `.env` local a partir de la plantilla y **reemplaza el secreto de ejemplo**:

```powershell
Copy-Item .env.example .env
notepad .env
```

Configura `SECRET_KEY` con un valor propio. Compose fuerza `DEBUG=False` en el backend, independientemente del valor local de esa variable. Si expones la aplicación con un hostname diferente de `localhost` o `127.0.0.1`, agrega ese hostname a `ALLOWED_HOSTS`. Después construye e inicia frontend y backend:

```powershell
docker compose up --build
```

La aplicación estará disponible en `http://localhost:8080` (o en el puerto indicado por `APP_PORT`). El endpoint de salud, pensado para comprobar disponibilidad y no para navegar la interfaz, está disponible en `http://localhost:8080/health` y `http://localhost:8080/health/`; responde JSON con el estado del backend. Nginx sirve los archivos compilados de React, entrega los medios desde el volumen compartido y reenvía las rutas `/books` y `/health` al backend dentro de la red privada de Compose. Solo se publica el puerto del frontend. El backend inicia con Gunicorn y aplica las migraciones antes de aceptar solicitudes.

SQLite y las imágenes subidas viven en los volúmenes nombrados `bookstore_data` y `bookstore_media`; se conservan al detener el stack:

```powershell
docker compose down
```

No uses una opción que elimine volúmenes si quieres conservar los datos locales. Docker Compose carga `.env` para sustituir sus variables, pero Django no interpreta directamente el archivo. La tasa `DEFAULT_EXCHANGE_RATE` de la plantilla sigue siendo ilustrativa. Para ejecutar el modo local descrito arriba no se requiere Docker.

## Estructura del repositorio

```text
backend/       Proyecto Django, API, modelo y tests
frontend/      SPA React/Vite
postman/       Colección Postman de la API
compose.yaml   Orquestación local opcional de contenedores
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
- [x] FASE 12 — Docker (opcional).

## Nota sobre el desarrollo

Mi experiencia profesional está principalmente orientada al desarrollo Full Stack con PHP y Laravel. Para esta prueba, Python y Django representaron un stack tecnológico nuevo para mí.

Durante el desarrollo utilicé herramientas de asistencia basadas en IA como apoyo para investigar y acelerar la implementación. La definición de la solución, las decisiones técnicas, la estructura de la aplicación y la validación de los resultados fueron dirigidas y revisadas por mí.

Esta prueba también representa mi capacidad de adaptarme rápidamente a un stack nuevo y trasladar conocimientos de desarrollo previamente adquiridos a una tecnología diferente.

Las reglas y el contexto ampliado de la prueba están en [Nextep_Prueba_Tecnica_Contexto_Copilot.md](./Nextep_Prueba_Tecnica_Contexto_Copilot.md).
