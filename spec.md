# spec.md — Especificación técnica

## Stack
- Frontend: React con Vite.
- Backend: Python con FastAPI.
- Base de datos: SQLite y SQLAlchemy.
- Agente: Gemini mediante google-genai.
- Visualización: Recharts.
- Pruebas: pytest y pruebas de compilación del frontend.

## Entidades
Producto: id, nombre, categoría, precio.

Venta: id, producto_id, cantidad, precio_unitario, fecha.

## Endpoints
- GET /api/productos
- POST /api/productos
- GET /api/ventas
- POST /api/ventas
- GET /api/indicadores
- POST /api/agente/chat

## Funcionalidades del agente
El agente debe disponer de herramientas de solo lectura:
- consultar_resumen_ventas()
- consultar_ventas_por_producto()
- consultar_ventas_por_categoria()

El agente podrá decidir qué herramienta utilizar según la pregunta del usuario.

## Reglas
- El navegador nunca accede directamente a Gemini.
- El backend valida los datos recibidos.
- Las consultas utilizan SQLAlchemy.
- El agente no ejecuta SQL arbitrario.
- Las herramientas no modifican registros.
- Las respuestas numéricas deben basarse en resultados de las herramientas.
- Las claves se almacenan en variables de entorno.

## Criterios de aceptación
- Los endpoints responden con JSON válido.
- Las ventas registradas persisten al reiniciar.
- El dashboard presenta los indicadores correctos.
- El agente puede responder preguntas utilizando herramientas.
- Los errores de Gemini se manejan sin exponer secretos.
- Existen pruebas automatizadas para las operaciones principales.