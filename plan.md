# plan.md — Plan de implementación

## Revisión de coherencia, dependencias y riesgos
- La Fase 2 es prerrequisito de las Fases 3 y 4: estas dependen de los datos y endpoints definidos allí.
- La Fase 1 se limita al scaffolding y configuración; no debe anticipar modelos, endpoints, dashboard ni integración Gemini.
- El stack declarado autoriza React/Vite, FastAPI, SQLAlchemy, Gemini, Recharts y pytest. No se agregan dependencias fuera de la especificación.
- Riesgos pendientes para fases posteriores: definir CORS y agregar autenticación/autorización antes de exponer los datos fuera de un entorno confiable; actualmente las rutas de datos no tienen autenticación.

## Fase 1 — Inicialización
- [x] Crear frontend React + Vite.
- [x] Crear backend FastAPI.
- [x] Configurar Git y .gitignore.
- [x] Instalar dependencias autorizadas del backend (FastAPI y pytest).
- [x] Instalar dependencias autorizadas del frontend (React, Vite y plugin de React; `frontend/package-lock.json`).
- [x] Verificar sintaxis e inicialización del backend.
- [x] Compilar frontend con Vite para producción.

## Fase 2 — Datos
- [x] Crear modelos Producto y Venta.
- [x] Configurar SQLite con SQLAlchemy.
- [x] Generar un seed determinista e idempotente de 50 ventas.
- [x] Implementar `GET/POST /api/productos`, `GET/POST /api/ventas` y `GET /api/indicadores`.
- [x] Validar payloads con Pydantic y relaciones de producto al registrar ventas.
- [x] Verificar APIs, persistencia, seed e indicadores con pytest.

### Evidencia de Fase 2
- `cd backend; python -m pytest -q` — 5 pruebas aprobadas.
- `python -m compileall -q backend\app backend\tests` y `git diff --check` — sin errores.
- Seed verificado: 50 ventas, 225 unidades, ingresos de 114825.00 y ticket promedio de 2296.50; los totales por categoría coinciden.
- `/api/agente/chat` permanece en la Fase 4, junto con la integración Gemini.

## Fase 3 — Frontend
- [x] Construir dashboard moderno y adaptable.
- [x] Mostrar KPIs de ingresos, unidades vendidas y ticket promedio, más gráfico por categoría.
- [x] Mostrar ventas recientes y formulario para registrar una venta.
- [x] Añadir estados de carga, error, reintento y validación del formulario.
- [x] Crear componentes reutilizables para tarjetas, secciones, tablas y errores.
- [x] Conectar el frontend exclusivamente a endpoints REST del backend; mantener el panel del agente como placeholder.
- [x] Ejecutar `npm run build` en `frontend/` — compilación de producción correcta.
- [x] Ejecutar `npm audit` — 0 vulnerabilidades.

### Evidencia de Fase 3
- Build Vite: salida de producción correcta; el gráfico de Recharts se carga en un chunk diferido.
- Las llamadas de datos son `GET /api/indicadores`, `GET /api/productos`, `GET /api/ventas` y `POST /api/ventas`; el proxy de desarrollo apunta a FastAPI en `127.0.0.1:8000`.
- El formulario y la tabla usan exclusivamente las respuestas de la API; el frontend no define ventas ni productos de demostración.
- El backend Uvicorn no está instalado en el entorno actual, por lo que la comprobación visual con datos servidos en vivo queda pendiente de iniciar FastAPI. No se agregó esa dependencia fuera del alcance autorizado.

## Fase 4 — Agente
- [x] Configurar el SDK oficial `google-genai`; modelo predeterminado `gemini-3.8-flash`, configurable con `GEMINI_MODEL`.
- [x] Leer `GEMINI_API_KEY` únicamente en el backend desde el entorno.
- [x] Implementar herramientas de solo lectura para resumen, ventas por producto y ventas por categoría mediante SQLAlchemy/SQLite.
- [x] Integrar function calling real con declaraciones tipadas, allowlist fija, validación de argumentos y llamadas automáticas deshabilitadas.
- [x] Crear `POST /api/agente/chat` con esquemas Pydantic para solicitud y respuesta.
- [x] Manejar configuración ausente, autenticación, cuotas, timeout, fallas del proveedor y respuestas sin texto.
- [x] Construir una interfaz conversacional que consulta únicamente el endpoint del backend.
- [x] Probar herramientas y endpoint con Gemini simulado, sin llamadas externas ni costos.

## Fase 5 — Calidad
- [ ] Ejecutar pytest.
- [ ] Compilar frontend.
- [ ] Validar manejo de errores.
- [ ] Revisar seguridad de secretos.
- [ ] Documentar ejecución en README.

### Evidencia de Fase 4
- `cd backend; python -m pytest -q` — 15 pruebas aprobadas; las pruebas del agente usan un cliente Gemini falso y SQLite de prueba.
- `python -m compileall -q backend\app backend\tests`, `git diff --check` y `python -m pip check` — sin errores ni requisitos rotos.
- `cd frontend; npm run build` — compilación de producción correcta; `npm audit` — 0 vulnerabilidades.
- El agente ejecuta exclusivamente las tres funciones declaradas; los argumentos inesperados se rechazan con Pydantic. No hay ejecución de SQL generada por el modelo.
- Los errores devueltos al cliente son mensajes controlados; no contienen claves ni excepciones del proveedor. No se hizo ninguna llamada a Gemini real.
- Hallazgo de seguridad pendiente: las rutas de lectura de datos aún no requieren autenticación; no se modificaron en esta fase.

### Configuración local de Gemini
- El backend carga `backend/.env` con `python-dotenv`; las variables ya definidas en el proceso tienen prioridad. El archivo está excluido por `.gitignore`.
- Verificación local: el archivo contiene una asignación no vacía para `GEMINI_API_KEY`; su valor no se mostró ni se versionó.

## Regla de trabajo
Codex/Chat debe implementar una fase a la vez, ejecutar las verificaciones correspondientes y actualizar este plan. No avanzar automáticamente si existen errores sin resolver.