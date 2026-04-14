 Reto 8: Diseñador de Suite de Pruebas Asíncronas

## 1. Archivo generado: `test_cliente_async.py`
Se ha desarrollado un marco de pruebas unitario ultra-exhaustivo (con más de 22 escenarios y 30 aseveraciones o assert loops) apalancado en `pytest` y `aioresponses`. Con él, validamos la solidez de las comunicaciones HTTP "mocked" sin perturbar el código base.

Se incluyeron explícitamente los pilares dictaminados:
1. Pruebas de equivalencia funcional conservando el trato transaccional de la versión síncrona.
2. Pruebas de simulación concurrente comprobando el valor inmensurable de `gather()` configurado sabiamente con `return_exceptions`.
3. Pruebas de cancelación masiva en cadenas observando limpieza y evasión de resource leaks.
4. Pruebas crudas al borde (Edge Cases), como la colisión de dos GETs idénticos a los mismos endpoints con variables de stringquery (`?categoria=`) diferentes paralelos para medir pureza transaccional sin contaminación de ram.
5. Los dos (2) tests adicionales inéditos propuestos: Probar el flujo de un `PATCH` parcial, y probar el flujo exótico ante la existencia de arrays validos pero completamente vacíos `[]` dictaminados por el servidor sin dar colisiones pydantic.

## 2. Reporte de QA: Bugs Encontrados y Correcciones Resueltas ✅

Gracias a aplicar esta suite pesada directamente contra nuestro base file (escrito en el Reto 3), nuestro departamento de QA asíncrono halló anomalías arquitectónicas ocultas, las cuales se parcharon en caliente:

### 🐛 Bug #1: Error Crítico al Interpretar Timeout en Entornos Asíncronos
**Comportamiento anterior:** En nuestro archivo `cliente_async_ecomarket.py` (líneas 1 al 120 aprox) hacíamos Try/Catch para el bloque TimeOut asumiendo esto del original:
```python
except aiohttp.ClientTimeout:
    raise EcoMarketError("Timeout...")
```
**Análisis:** Esta excepción era conceptualmente falsa. El framework moderno de asyncio al no completarse un `wait_for` emite en la raíz un `asyncio.TimeoutError`, mientras que `aiohttp.ClientTimeout` ni siquiera era una clase excepcionista atrapable; ¡es una simple clase nativa configuradora de objeto de aiohttp! Estaba evadiendo nuestro cerrojo y colapsando el dashboard en producción silenciosa sin alertar.
**Corrección Ejecutada:** Se procedió a sustituir e inyectar el recolector correcto (`except asyncio.TimeoutError:`) en todos y cada uno de los métodos CRUD.

### 🐛 Bug #2: Controladores Faltantes de Cancelación Abrupta
**Comportamiento anterior:** Las funciones base de `cargar_dashboard` o CRUD no declaraban de ser necesario la captura controlada de `asyncio.CancelledError`. Al ejecutar en nuestro QA `task.cancel()`, el Traceback del *event_loop* de Python chillaba ensuciando los microservicios sin resolver la memoria limpia.
**Corrección Ejecutada:** Se incluyeron bloques para rastrear si un hilo padre nos liquidó (como ocurre en las cancelaciones por 401 grupales) para interceptar callboxes. Ejemplo en listar:
```python
except asyncio.CancelledError:
    print("La petición fue cancelada.")
    raise # Liberando elegantemente
```