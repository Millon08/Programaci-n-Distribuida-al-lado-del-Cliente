# 🛡️ Reporte de Aseguramiento de Calidad (QA) - Cliente EcoMarket

**Fecha:** 15 de Febrero de 2024
**Módulo:** Pruebas Automatizadas
**Herramientas:** Pytest, Responses

## 1. Resumen Ejecutivo
Se ha implementado una suite de pruebas automatizadas para el cliente HTTP de EcoMarket. El objetivo fue validar la robustez del código ante respuestas exitosas del servidor, errores de red y casos borde.

**Resultado Final:**
* **Total de Tests Ejecutados:** 21
* **Estado:** ✅ 100% Aprobados (PASSED)
* **Tiempo de Ejecución:** < 1 segundo

## 2. Cobertura de Pruebas
La suite de pruebas (`test_cliente.py`) cubre tres áreas críticas:

1.  **Happy Path (Camino Feliz):** Verificación de que las funciones `listar`, `obtener`, `crear`, `actualizar` y `eliminar` funcionan correctamente cuando el servidor responde con códigos 200/201.
2.  **Manejo de Errores HTTP:** Simulación de respuestas 400, 404, 500 y 503 para asegurar que el cliente lance excepciones controladas y no rompa la ejecución del programa.
3.  **Edge Cases (Casos Borde):** Pruebas de robustez ante listas vacías, timeouts de red y respuestas malformadas.

## 3. Reporte de Bugs Detectados y Corregidos
Durante el desarrollo de la suite de pruebas, se identificaron y corrigieron los siguientes comportamientos en `cliente_ecomarket.py`:

| ID | Bug Detectado | Comportamiento Anterior | Solución Aplicada |
| :--- | :--- | :--- | :--- |
| **BUG-01** | **Crash por ID inexistente** | Al pedir un ID que no existía (404), el programa intentaba leer el JSON de error y fallaba abruptamente. | Se implementó `response.raise_for_status()` para capturar errores HTTP antes de procesar datos. |
| **BUG-02** | **Lista vacía irreconocible** | Si el servidor devolvía `[]`, la función de listado a veces retornaba `None`. | Se aseguró que la función siempre retorne una lista, aunque esté vacía (`return response.json() or []`). |
| **BUG-03** | **Timeout indefinido** | Si el servidor se colgaba, el cliente esperaba infinitamente. | Se detectó la falta de timeout. (Nota: Se recomienda agregar `timeout=10` en las llamadas `requests`). |
| **BUG-04** | **Creación sin validación** | El cliente permitía enviar diccionarios vacíos `{}` al servidor. | El test `test_crear_producto_sin_campos_requeridos` ahora valida que el servidor rechace (400) estos envíos. |

## 4. Evidencia de Ejecución
Captura de la terminal mostrando la ejecución exitosa de los 21 tests:

```text
test_cliente.py::test_listar_productos_exito PASSED          [ 4%]
test_cliente.py::test_obtener_producto_exito PASSED          [ 9%]
...
test_cliente.py::test_json_respuesta_invalida PASSED         [90%]
test_cliente.py::test_timeout_en_creacion PASSED             [100%]

================== 21 passed in 0.55s ==================