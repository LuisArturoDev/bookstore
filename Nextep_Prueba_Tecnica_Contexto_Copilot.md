# Contexto de desarrollo — Prueba Técnica Nextep Innovation

## 1. Objetivo del proyecto

Construir una aplicación Full Stack para gestionar el inventario de una librería.

La prueba solicita desarrollar:

- Una API REST para gestionar libros.
- Persistencia de datos.
- Validaciones de negocio.
- Integración con una API externa de tasas de cambio.
- Cálculo del precio de venta sugerido.
- Una SPA que consuma la API.
- Manejo de estados de carga y errores.
- Documentación del proyecto.
- Colección de Postman.
- Repositorio Git con historial de commits.
- Dockerización como PLUS.

La prueba indica que Django es el framework preferido para el backend.

> IMPORTANTE: Este proyecto se debe construir progresivamente. No generar toda la aplicación de una sola vez. Cada fase debe quedar funcional antes de continuar con la siguiente.

---

# 2. Objetivo de aprendizaje y desarrollo

El desarrollador tiene experiencia principalmente con PHP/Laravel, pero Django es una tecnología nueva para este proyecto.

Por eso, el agente debe:

1. Construir la aplicación de forma incremental.
2. Explicar brevemente las decisiones importantes.
3. Relacionar conceptos de Django con conceptos equivalentes de Laravel cuando sea útil.
4. Evitar abstracciones innecesarias.
5. Mantener una arquitectura clara y profesional.
6. No introducir tecnologías que no sean necesarias.
7. No ocultar errores mediante soluciones improvisadas.
8. No generar código que el desarrollador no pueda explicar.

El objetivo no es solamente conseguir una aplicación funcional, sino comprender cómo está construida.

## 2.1. Cómo explicar y avanzar por fases

La explicación es parte del entregable de cada fase, no un resumen opcional al final. Antes de cada bloque de implementación, explicar en lenguaje sencillo:

1. Qué problema resuelve y para qué sirve.
2. Qué se va a cambiar y en qué archivos/capas.
3. Por qué se eligió esa solución frente a una alternativa sencilla.
4. Qué hace cada pieza y cómo se relaciona con Django/DRF o React; comparar con Laravel cuando ayude.
5. Cómo se comprobará que funciona y qué resultado se espera.

Al cerrar cada fase, informar los cambios efectivamente realizados, los comandos ejecutados, las pruebas y resultados, las decisiones tomadas o pendientes y el siguiente paso recomendado. No afirmar que algo funciona si no se verificó. No comenzar la siguiente fase hasta recibir confirmación explícita del usuario.

Si una decisión cambia el comportamiento o el alcance y no está definida aquí, señalarla antes de implementarla y pedir confirmación; no ocultarla como un detalle técnico.

---

# 3. Stack esperado

## Backend

- Python
- Django
- Django REST Framework
- Base de datos relacional
- `requests` o cliente HTTP equivalente para la API externa

## Frontend

Se puede utilizar:

- React
- Angular
- Vue
- Svelte

Preferencia para este proyecto:

- React
- Vite
- JavaScript o TypeScript

La elección final debe mantenerse sencilla y adecuada al alcance de la prueba.

## Otros

- Git
- GitHub/GitLab u otro repositorio
- Postman
- Docker como mejora opcional/PLUS
- Variables de entorno mediante `.env`

---

# 4. Arquitectura general

La aplicación debe seguir aproximadamente esta arquitectura:

```text
                    ┌─────────────────────┐
                    │     React SPA       │
                    │                     │
                    │ Dashboard           │
                    │ CRUD de libros      │
                    │ Filtros             │
                    │ Cálculo de precio   │
                    └──────────┬──────────┘
                               │ HTTP/JSON
                               ▼
                    ┌─────────────────────┐
                    │   Django + DRF      │
                    │                     │
                    │ Books API           │
                    │ Validaciones        │
                    │ Price calculation   │
                    └──────┬───────┬──────┘
                           │       │
                           │       └──────────────────┐
                           ▼                          ▼
                    ┌──────────────┐        ┌──────────────────┐
                    │  Database    │        │ Exchange Rate    │
                    │              │        │ API externa      │
                    │ Books        │        │                  │
                    └──────────────┘        └──────────────────┘
```

La lógica de cálculo de precio debe evitar quedar completamente dentro de la vista/controlador.

Conceptualmente:

```text
Book
  ↓
PriceCalculationService
  ↓
ExchangeRateService
  ↓
API externa
  ↓
Tasa de cambio
  ↓
Costo en moneda local
  ↓
Margen 40%
  ↓
Actualizar libro
  ↓
Respuesta API
```

---

# 5. Modelo Book

El modelo principal es `Book`.

La prueba proporciona el siguiente ejemplo:

```json
{
  "id": 1,
  "title": "El Quijote",
  "author": "Miguel de Cervantes",
  "isbn": "978-84-376-0494-7",
  "cost_usd": 15.99,
  "selling_price_local": null,
  "stock_quantity": 25,
  "category": "Literatura Clásica",
  "supplier_country": "ES",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

Campos:

- `id`
- `title`
- `author`
- `isbn`
- `cost_usd`
- `selling_price_local`
- `stock_quantity`
- `category`
- `supplier_country`
- `created_at`
- `updated_at`

Contrato inicial de campos:

- Al crear un libro, `title`, `author`, `isbn`, `cost_usd`, `stock_quantity`, `category` y `supplier_country` son obligatorios.
- `selling_price_local` se inicia como nulo y solo se modifica mediante el cálculo de precio; el cliente no puede asignarlo directamente en el CRUD.
- `supplier_country` utiliza un código de país ISO 3166-1 alpha-2 en mayúsculas (por ejemplo, `ES`).
- `created_at` y `updated_at` los genera el servidor y se exponen en ISO 8601 con zona horaria UTC.

---

# 6. Reglas del modelo

Se deben cumplir las siguientes reglas indicadas por la prueba:

## cost_usd

Debe ser mayor que 0.

```text
cost_usd > 0
```

## stock_quantity

No puede ser negativo.

```text
stock_quantity >= 0
```

## ISBN

Debe ser un ISBN-10 o ISBN-13 válido, incluyendo la comprobación de su dígito de control; no basta con que tenga la longitud correcta.

Además:

- No puede existir otro libro con el mismo ISBN.

## ISBN y guiones

La prueba muestra un ISBN como:

```text
978-84-376-0494-7
```

Contrato de normalización:

1. Aceptar guiones y espacios en la entrada.
2. Quitarlos antes de validar; ISBN-10 permite `X` únicamente como último carácter.
3. Validar longitud, caracteres y dígito de control.
4. Guardar y comparar la forma normalizada (sin separadores y con `X` en mayúscula), para que distintas presentaciones del mismo ISBN no eludan la unicidad.
5. Devolver esa forma normalizada en la API. La interfaz puede mostrarla con formato legible, pero no cambia el valor almacenado.

La validación del serializer ofrece errores claros al cliente y la restricción única de la base de datos protege la integridad ante solicitudes concurrentes.

## Precisión monetaria

- Representar cantidades monetarias y tasas con decimales (`Decimal`), nunca con `float`.
- Aceptar `cost_usd` con hasta dos decimales y mayor que cero.
- Mantener precisión decimal durante las operaciones; redondear `cost_local` y `selling_price_local` a dos decimales usando `ROUND_HALF_UP`.
- Persistir el precio sugerido con dos decimales. El mismo criterio debe usarse en la respuesta de la API y en las pruebas.

---

# 7. Endpoints obligatorios

La API debe implementar:

Las rutas siguientes son las rutas HTTP exactas del contrato inicial: no llevan prefijo `/api` ni barra final. Configurar Django/DRF para respetarlas y usar las mismas rutas en frontend, pruebas, README y Postman.

## Crear libro

```http
POST /books
```

## Listar libros

```http
GET /books
```

Debe soportar la paginación requerida por el frontend.

Contrato de paginación: usar paginación por número de página, con `page` y `page_size`; tamaño predeterminado de 10 y máximo de 100. La respuesta incluye `count`, `next`, `previous` y `results`, según el formato estándar de DRF.

## Obtener libro

```http
GET /books/{id}
```

## Actualizar libro

```http
PUT /books/{id}
```

## Eliminar libro

```http
DELETE /books/{id}
```

---

# 8. Endpoints opcionales solicitados por la prueba

Aunque están marcados como opcionales en la sección de CRUD, el frontend requiere funcionalidades equivalentes de búsqueda, categorías y stock bajo.

Por lo tanto, implementarlos para que el frontend pueda cumplir completamente sus requisitos.

## Buscar/filtrar por categoría

```http
GET /books/search?category={category}
```

## Libros con stock bajo

```http
GET /books/low-stock?threshold=10
```

El umbral debe ser un entero no negativo; un libro se considera de stock bajo cuando `stock_quantity <= threshold`. La búsqueda por categoría recorta espacios en los extremos y compara el nombre sin distinguir mayúsculas/minúsculas. Un filtro válido sin coincidencias devuelve una lista vacía, no un error.

La implementación puede evolucionar hacia un sistema de filtros más unificado si resulta más limpio, por ejemplo:

```http
GET /books?category=Literatura&low_stock=true&threshold=10
```

Pero no romper los endpoints requeridos sin una razón clara.

---

# 9. Endpoint principal de negocio

La prueba requiere:

```http
POST /books/{id}/calculate-price
```

Este endpoint debe:

1. Obtener el libro.
2. Leer `cost_usd`.
3. Consultar la tasa de cambio actual USD → moneda local.
4. Convertir el costo.
5. Aplicar un margen de beneficio del 40%.
6. Actualizar `selling_price_local`.
7. Guardar el resultado.
8. Devolver información detallada del cálculo.

---

# 10. API externa

La prueba proporciona:

```text
https://api.exchangerate-api.com/v4/latest/USD
```

La aplicación debe utilizar esta API para obtener la tasa de cambio.

No colocar la URL directamente en múltiples lugares del proyecto.

Preferiblemente centralizarla mediante configuración/variables de entorno.

Ejemplo conceptual:

```env
EXCHANGE_RATE_API_URL=https://api.exchangerate-api.com/v4/latest/USD
```

---

# 11. Cálculo del precio

La prueba indica:

```text
1. cost_usd
2. obtener USD → moneda local
3. convertir costo a moneda local
4. aplicar 40% de margen
5. guardar selling_price_local
```

Fórmula conceptual:

```text
cost_local = cost_usd × exchange_rate

selling_price_local = cost_local × 1.40
```

Ejemplo de la prueba:

```text
cost_usd = 15.99
exchange_rate = 0.85

cost_local = 15.99 × 0.85
cost_local = 13.5915

selling_price_local = 13.5915 × 1.40
selling_price_local = 19.0281
```

El resultado esperado se muestra redondeado como:

```text
19.03
```

La política de redondeo debe ser consistente en toda la aplicación.

---

# 12. Respuesta esperada del cálculo

La prueba muestra una respuesta con esta estructura:

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
  "calculation_timestamp": "2025-01-15T10:30:00Z"
}
```

Para este alcance no implementar conversión multidivisa: usar una sola moneda local, configurable mediante `LOCAL_CURRENCY`, con `EUR` como valor inicial tomado del ejemplo de la prueba. La tasa solicitada a la API externa debe corresponder a esa moneda. Si se desea otra moneda, se cambia la configuración; no se añade una entidad o flujo de monedas.

`cost_local` y `selling_price_local` se devuelven redondeados a dos decimales con la regla definida en “Precisión monetaria”. `calculation_timestamp` es la hora UTC en que se realizó el cálculo, no la fecha de creación del libro.

---

# 13. Manejo de errores

La prueba requiere manejar apropiadamente:

```text
400 Bad Request
404 Not Found
500 Internal Server Error
503 Service Unavailable
```

## 400

Utilizar para errores de entrada/validación.

Ejemplos:

- cost_usd inválido
- stock negativo
- ISBN inválido
- ISBN duplicado
- datos obligatorios faltantes

## 404

Cuando el libro solicitado no existe.

## 503

Cuando la dependencia externa no está disponible y no se puede completar la operación de forma normal.

Como la prueba exige una tasa de respaldo, un fallo de la API externa no causa por sí solo un 503: si el fallback configurado es válido, completar el cálculo con él y señalarlo en la respuesta. Devolver 503 solo si no se puede obtener una tasa válida ni hay un fallback válido disponible.

## 500

Para errores inesperados del servidor que no correspondan a errores controlados.

No capturar todas las excepciones y convertirlas indiscriminadamente en 500 sin registrar/conservar información útil.

---

# 14. Fallback de tasa de cambio

La prueba establece:

> Si la API de tasas de cambio falla, utilizar una tasa por defecto.

Esto debe implementarse explícitamente.

Conceptualmente:

```text
Intentar obtener tasa
       │
       ├── Éxito → usar tasa actual
       │
       └── Error → usar tasa por defecto
```

La tasa por defecto debe estar configurada y no hardcodeada en múltiples partes del código.

Ejemplo conceptual:

```env
DEFAULT_EXCHANGE_RATE=0.85
```

`0.85` es únicamente el valor inicial ilustrativo tomado del ejemplo de la prueba; no representa una cotización vigente. Mantenerlo configurable y documentar que el fallback se aplica a la moneda indicada por `LOCAL_CURRENCY`. La respuesta de cálculo debe incluir `used_fallback` (booleano) para que el consumidor sepa si se utilizó la tasa de respaldo.

---

# 15. Servicios recomendados

Separar la integración externa de la lógica principal.

Una estructura conceptual:

```text
services/
├── exchange_rate_service
└── price_calculation_service
```

## ExchangeRateService

Responsabilidad:

- Consultar la API externa.
- Interpretar la respuesta.
- Obtener la tasa USD → moneda local.
- Gestionar timeout/errores de conexión.
- Aplicar fallback cuando corresponda.

No debe:

- Modificar libros.
- Calcular precios de venta.

## PriceCalculationService

Responsabilidad:

- Recibir un libro.
- Obtener la tasa mediante ExchangeRateService.
- Calcular costo local.
- Aplicar margen.
- Guardar selling_price_local.
- Construir el resultado del cálculo.

Esto permite mantener separadas las responsabilidades.

---

# 16. Serializers / validación

En Django REST Framework utilizar serializers para:

- Validar entrada.
- Serializar objetos.
- Definir campos.
- Devolver datos consistentes.

No duplicar las mismas validaciones en múltiples endpoints.

La validación debe estar lo más cerca posible de la capa responsable.

---

# 17. Django vs Laravel — mapa mental

El desarrollador viene principalmente de Laravel.

Utilizar esta equivalencia para facilitar el aprendizaje:

| Laravel | Django / DRF |
|---|---|
| `php artisan` | `python manage.py` |
| Model | Model |
| Eloquent | Django ORM |
| Migration | Migration |
| Controller | View / APIView / ViewSet |
| Form Request | Serializer validation |
| Resource | Serializer |
| Route | URL patterns / Router |
| `.env` | Variables de entorno |
| Middleware | Middleware |
| Service class | Service class |
| `php artisan migrate` | `python manage.py migrate` |
| `php artisan make:model` | `python manage.py startapp` + creación del model |
| `composer` | `pip` / `requirements.txt` |

No intentar convertir Django en una copia de Laravel. Utilizar las convenciones propias de Django.

---

# 18. Frontend SPA

El frontend debe consumir la API.

Debe permitir:

## Dashboard

Mostrar:

- listado de libros
- título
- autor
- ISBN
- categoría
- costo
- precio de venta
- stock
- acciones

Debe existir paginación backend.

## Filtros

Permitir:

- búsqueda/categoría
- visualización de stock bajo

## Crear libro

Formulario con validaciones para:

- título
- autor
- ISBN
- costo
- stock
- categoría
- país del proveedor

Las validaciones del frontend no reemplazan las del backend.

## Editar libro

Permitir actualizar los datos.

## Eliminar libro

Debe mostrar confirmación antes de eliminar.

## Calcular precio

Debe existir un botón visible:

```text
Calcular precio de venta
```

Al ejecutarlo:

1. Mostrar loading.
2. Llamar a `/books/{id}/calculate-price`.
3. Mostrar resultado.
4. Actualizar la información del libro.
5. Mostrar error si falla.

El resultado debe mostrar al menos:

- costo USD
- tasa de cambio
- costo local
- margen
- precio final
- moneda

---

# 19. Estados de interfaz

La SPA debe contemplar:

```text
Loading
Success
Error
Empty
```

Ejemplo:

```text
Cargando libros...
```

Errores:

```text
No se pudo cargar el inventario.
```

Éxito:

```text
Precio calculado correctamente.
```

No utilizar solamente `console.log()` para informar errores al usuario.

Utilizar toasts, alerts o un sistema visual equivalente.

---

# 20. Estructura sugerida del backend

No es obligatorio utilizar exactamente esta estructura, pero debe mantenerse una separación razonable:

```text
backend/
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
└── books/
    ├── migrations/
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── services/
    │   ├── exchange_rate_service.py
    │   └── price_calculation_service.py
    ├── tests/
    └── ...
```

No crear carpetas solamente por seguir una arquitectura de moda.

Si una separación no aporta valor para este proyecto, mantenerla simple.

---

# 21. Estructura sugerida del frontend

Ejemplo:

```text
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   └── App.*
├── package.json
└── ...
```

Posible organización:

```text
components/
├── BookTable
├── BookForm
├── BookModal
├── PriceCalculation
├── Loading
└── Notification

pages/
├── Dashboard
└── BookDetails

services/
└── booksApi
```

Adaptar la estructura a la complejidad real del proyecto.

---

# 22. Fases de implementación

## FASE 0 — Preparación

Objetivo:

Crear el repositorio y estructura inicial.

Tareas:

- Crear repositorio.
- Definir la estructura raíz y dónde residirán `backend/` y `frontend/`, sin inicializar aún sus aplicaciones.
- Crear `.gitignore`.
- Crear `.env.example`.
- Crear README inicial.
- Confirmar el stack y las decisiones configurables que afectan el contrato (moneda local y tasa de fallback).
- Realizar primer commit.

Commit sugerido:

```text
chore: initialize project structure
```

No implementar todavía toda la funcionalidad.

Esta fase prepara el repositorio y deja documentadas las decisiones de arranque; no crea todavía el proyecto Django ni React. Django se inicializa en FASE 1 y React/Vite en FASE 8, para que cada base tecnológica se explique y verifique en su propia fase.

---

# FASE 1 — Django básico

Objetivo:

Entender y dejar funcionando Django.

Tareas:

- Crear proyecto Django.
- Crear app `books`.
- Configurar Django REST Framework.
- Configurar base de datos.
- Ejecutar servidor.
- Crear primer endpoint de prueba.
- Verificar que la API responde.

Antes de continuar:

- El proyecto debe iniciar correctamente.
- El endpoint debe responder correctamente.

---

# FASE 2 — Modelo Book

Objetivo:

Crear el modelo y persistencia.

Tareas:

- Crear `Book`.
- Definir campos.
- Definir tipos.
- Definir restricciones.
- Configurar timestamps.
- Crear migration.
- Ejecutar migration.
- Verificar datos en la base.

Implementar unicidad de ISBN.

Después:

- Crear serializer.
- Probar serialización.

Commit sugerido:

```text
feat: add book model and serializer
```

---

# FASE 3 — CRUD

Implementar:

```text
POST /books
GET /books
GET /books/{id}
PUT /books/{id}
DELETE /books/{id}
```

Agregar:

- serializers
- validaciones
- respuestas HTTP
- manejo de 404
- paginación

Probar cada endpoint con Postman.

No continuar hasta que el CRUD sea estable.

Commit sugerido:

```text
feat: implement books CRUD API
```

---

# FASE 4 — Filtros

Implementar:

```text
GET /books/search?category={category}
GET /books/low-stock?threshold=10
```

Verificar:

- categoría existente
- categoría sin resultados
- threshold válido
- stock = 0
- stock menor al threshold

Commit sugerido:

```text
feat: add inventory filters
```

---

# FASE 5 — Integración de Exchange Rate

Crear:

```text
ExchangeRateService
```

Responsabilidades:

- llamar API externa
- timeout
- interpretar respuesta
- obtener tasa
- detectar errores
- fallback

Antes de conectarlo al cálculo:

Crear pruebas aisladas para:

1. API exitosa.
2. API con error.
3. API con respuesta inválida.
4. Timeout.

Commit sugerido:

```text
feat: add exchange rate service
```

---

# FASE 6 — Cálculo del precio

Crear:

```text
PriceCalculationService
```

Implementar:

```text
cost_local = cost_usd × exchange_rate

selling_price_local = cost_local × 1.40
```

Actualizar:

```text
selling_price_local
```

Crear:

```http
POST /books/{id}/calculate-price
```

Probar:

- libro existente
- libro inexistente
- costo válido
- API externa funcionando
- API externa fallando
- fallback
- redondeo

Commit sugerido:

```text
feat: implement selling price calculation
```

---

# FASE 7 — Tests

Crear tests para:

## Modelo

- ISBN único.
- stock no negativo.
- costo mayor a cero.

## API

- crear libro
- listar libros
- obtener libro
- actualizar libro
- eliminar libro
- libro inexistente
- datos inválidos
- ISBN duplicado

## Price calculation

- cálculo correcto
- actualización de precio
- API externa exitosa
- fallback
- error controlado

No depender de la API externa real para todos los tests.

Mockear la dependencia externa cuando sea apropiado.

Commit sugerido:

```text
test: add backend test coverage
```

---

# FASE 8 — Frontend

Construir la SPA.

Orden recomendado:

1. Configuración del proyecto.
2. Servicio HTTP.
3. Dashboard.
4. Tabla/listado.
5. Paginación.
6. Filtros.
7. Crear libro.
8. Editar libro.
9. Eliminar libro.
10. Cálculo de precio.
11. Loading.
12. Errores.
13. Notificaciones.

No construir todas las pantallas simultáneamente.

---

# FASE 9 — Integración completa

Verificar el flujo completo:

```text
Usuario
  ↓
React
  ↓
POST /books
  ↓
Django
  ↓
Database
```

Y:

```text
Usuario
  ↓
"Calcular precio"
  ↓
React
  ↓
POST /books/{id}/calculate-price
  ↓
Django
  ↓
PriceCalculationService
  ↓
ExchangeRateService
  ↓
API externa
  ↓
Cálculo
  ↓
Database
  ↓
React
  ↓
Resultado visual
```

Probar errores en cada punto.

---

# FASE 10 — Postman

Crear una colección Postman con:

```text
Books
├── Create Book
├── List Books
├── Get Book
├── Update Book
├── Delete Book
├── Search by Category
├── Low Stock
└── Calculate Price
```

Agregar ejemplos de requests y respuestas cuando sea útil.

---

# FASE 11 — README

El README final debe explicar:

## Requisitos

- Python
- Node.js
- npm
- base de datos
- Docker si se utiliza

## Backend

Cómo instalar:

```text
crear entorno virtual
instalar dependencias
configurar .env
ejecutar migraciones
iniciar servidor
```

## Frontend

Cómo instalar dependencias y ejecutar.

## Variables de entorno

Documentar `.env.example`.

## API

Documentar endpoints.

## Ejemplo de uso

Incluir ejemplos JSON.

## Tests

Indicar cómo ejecutar tests.

## Postman

Indicar dónde está la colección.

---

# FASE 12 — Docker

Esta fase es PLUS.

Si el proyecto está estable:

- Dockerfile backend.
- Dockerfile frontend si corresponde.
- docker-compose.
- configuración de base de datos.
- variables de entorno.

No introducir Docker antes de que la aplicación funcione correctamente.

---

# 23. Git

Realizar commits pequeños y descriptivos.

Ejemplos:

```text
chore: initialize project
feat: add book model
feat: implement books CRUD API
feat: add inventory filters
feat: add exchange rate service
feat: implement price calculation
test: add backend tests
feat: add React dashboard
feat: add book management forms
feat: add price calculation UI
docs: update README
chore: add docker configuration
```

Evitar:

```text
update
changes
fix stuff
final
final2
final-final
```

No hacer un único commit gigantesco con toda la aplicación.

---

# 24. Variables de entorno

Utilizar `.env` para configuración.

Ejemplo:

```env
DEBUG=True
SECRET_KEY=change-me
EXCHANGE_RATE_API_URL=https://api.exchangerate-api.com/v4/latest/USD
LOCAL_CURRENCY=EUR
DEFAULT_EXCHANGE_RATE=0.85
```

El archivo `.env` real no debe subirse al repositorio.
`DEFAULT_EXCHANGE_RATE` es un fallback de ejemplo, no una cotización actual. Debe corresponder a `LOCAL_CURRENCY`.

Crear:

```text
.env.example
```

---

# 25. Seguridad básica

Aunque sea una prueba técnica, aplicar buenas prácticas:

- No subir secretos.
- No subir `.env`.
- No hardcodear credenciales.
- Validar entradas.
- No confiar en validaciones únicamente del frontend.
- Manejar errores.
- Configurar CORS de manera razonable para desarrollo.
- No exponer información sensible en errores.

---

# 26. Decisiones que deben evitarse

No:

- instalar muchas dependencias innecesarias
- crear microservicios
- usar una arquitectura excesivamente compleja
- introducir autenticación si no es requerida
- crear un sistema de roles si no es requerido
- implementar múltiples monedas completas si no es necesario
- agregar funcionalidades fuera del alcance sin razón
- duplicar lógica entre frontend y backend
- colocar toda la lógica de negocio en las views
- confiar únicamente en la API externa real durante los tests

El proyecto debe demostrar criterio técnico, no cantidad de código.

---

# 27. Criterio para usar IA

El agente de Copilot puede:

- generar código inicial
- sugerir estructura
- explicar errores
- crear tests
- refactorizar
- ayudar con documentación

Pero cada implementación debe poder explicarse.

Antes de agregar una funcionalidad importante, explicar brevemente:

1. Qué problema resuelve.
2. Qué archivo/capa se modifica.
3. Por qué se coloca allí.
4. Cómo se relaciona con Django/DRF.
5. Cómo probarlo.

No generar código masivo sin explicar qué se está construyendo.

---

# 28. Regla de trabajo para Copilot

IMPORTANTE:

Trabajar solamente en la fase solicitada.

Si el usuario dice:

```text
Implementemos FASE 2
```

Antes de tocar archivos, explicar qué se busca conseguir en esa fase, para qué sirve, por qué se usará el enfoque propuesto, qué piezas se crearán/modificarán y cómo se validarán. Explicar cada bloque coherente de cambios antes de realizarlo; no asumir que una lista de archivos sustituye la explicación.

No implementar automáticamente:

- CRUD completo
- integración externa
- frontend
- Docker
- tests de todo el sistema

Completar solo FASE 2 y verificarla.

Después mostrar:

```text
Objetivo y propósito:
- ...

Decisiones y por qué:
- ...

Implementado:
- ...
- ...

Archivos modificados:
- ...

Qué hace cada parte:
- ...

Comandos ejecutados y resultado:
- ...

Cómo probar:
- ...

Conceptos aprendidos (incluida comparación con Laravel cuando aporte):
- ...

Siguiente fase:
- ...
```

Si una prueba no se ejecutó o falló, indicarlo junto con la causa; no presentarlo como verificado. Esperar confirmación antes de avanzar a otra fase.

---

# 29. Estado inicial esperado

El proyecto comienza sin implementación completa.

El objetivo inmediato es:

```text
FASE 0
↓
FASE 1
↓
FASE 2
↓
FASE 3
...
```

No saltarse fases sin una razón clara.

---

# 30. Definition of Done

La prueba se considera terminada cuando:

- [ ] Backend Django funcional.
- [ ] API REST funcional.
- [ ] CRUD de libros.
- [ ] Validaciones.
- [ ] ISBN único.
- [ ] Búsqueda/categoría.
- [ ] Low stock.
- [ ] Paginación.
- [ ] Integración con exchange-rate API.
- [ ] Fallback de tasa.
- [ ] Cálculo de margen del 40%.
- [ ] Actualización del precio.
- [ ] Manejo de errores.
- [ ] Tests backend.
- [ ] SPA funcional.
- [ ] Dashboard.
- [ ] Formularios.
- [ ] Eliminación con confirmación.
- [ ] Cálculo de precio desde frontend.
- [ ] Loading states.
- [ ] Notificaciones/errores.
- [ ] README.
- [ ] Colección Postman.
- [ ] `.env.example`.
- [ ] Git organizado.
- [ ] Docker (PLUS).

---

# 31. Primera tarea para el agente

NO implementar toda la aplicación.

Comenzar únicamente con:

## FASE 0 — Preparación

1. Revisar este documento y explicar el alcance de FASE 0.
2. Confirmar el stack propuesto y la estructura raíz.
3. Confirmar `LOCAL_CURRENCY` y el valor inicial de fallback; registrar que el fallback no es una cotización vigente.
4. Crear `.gitignore`, `.env.example` y README inicial.
5. Inicializar el repositorio Git si aún no existe.
6. No inicializar todavía Django, DRF, React ni Vite; corresponden a sus fases respectivas.
7. No implementar todavía el CRUD, la integración externa ni el cálculo de precio.

Al terminar FASE 0, explicar:

- objetivo y propósito de cada archivo/carpeta creada
- decisiones tomadas y motivo
- comandos utilizados y resultado
- cómo comprobar el estado de la fase
- qué queda explícitamente fuera de alcance
- siguiente paso recomendado

Luego esperar instrucciones para continuar.

---

# 32. Regla final

La prioridad es:

```text
Comprensión
    ↓
Código limpio
    ↓
Funcionalidad
    ↓
Tests
    ↓
Documentación
    ↓
Mejoras
```

No priorizar velocidad de generación sobre comprensión.

La aplicación debe ser suficientemente profesional para una prueba técnica de Full Stack, pero suficientemente sencilla para que el desarrollador pueda defender cada decisión durante una entrevista.
