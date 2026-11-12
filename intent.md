# intent.md — InsightDesk AI

## Problema de negocio
Una empresa comercial necesita consultar sus ventas, identificar productos de alto y bajo rendimiento y obtener recomendaciones basadas en datos.

Actualmente, el análisis requiere conocimientos técnicos y consultas manuales.

## Objetivo
Desarrollar una aplicación Full-Stack que permita gestionar ventas y consultar indicadores mediante un agente de inteligencia artificial integrado con Gemini.

## Usuarios
- Gerente comercial.
- Analista de ventas.
- Administrador del sistema.

## Capacidades principales
1. Registrar productos y ventas.
2. Visualizar indicadores comerciales.
3. Consultar información mediante lenguaje natural.
4. Obtener recomendaciones fundamentadas en datos.
5. Mantener el control de las operaciones en el backend.

## Criterios de éxito
- El usuario puede registrar y consultar ventas.
- Los indicadores coinciden con los datos almacenados.
- El agente puede invocar herramientas para consultar la información.
- El agente no inventa cifras cuando faltan datos.
- La API key no queda expuesta al navegador.

## Restricciones
El sistema debe utilizar React, FastAPI, SQLite y Gemini. Se priorizará una arquitectura modular, segura y verificable.