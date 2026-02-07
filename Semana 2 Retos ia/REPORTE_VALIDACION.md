# 🛡️ Reporte de Validación de Datos - Semana 2

**Autor:**  Jose Emiliano
**Fecha:** 6 de Febrero, 2026

---

## 1. Comparativa de Estrategias de Validación

Análisis de ventajas y desventajas para el caso de uso de EcoMarket.

| Estrategia | Ventajas | Desventajas | Veredicto para EcoMarket |
| :--- | :--- | :--- | :--- |
| **Validación Manual (`if/else`)** | • Rendimiento máximo (muy rápido).<br>• No requiere instalar librerías externas.<br>• Control total sobre el mensaje de error. | • Código extenso y difícil de leer (espagueti).<br>• Mantenimiento costoso si el JSON crece.<br>• Fácil cometer errores humanos. | Útil solo para prototipos rápidos o scripts sin dependencias. |
| **Pydantic (Modelos Tipados)** | • Sintaxis limpia y moderna.<br>• Validación y conversión de tipos automática.<br>• Estándar actual en Python (FastAPI). | • Curva de aprendizaje inicial.<br>• Es una dependencia pesada extra. | **Opción recomendada** para la versión productiva de la API. |
| **JSON Schema** | • Estándar universal (sirve para Frontend y Backend).<br>• Excelente para documentación automática.<br>• Portabilidad entre lenguajes. | • Sintaxis muy verbosa y compleja de escribir.<br>• Validación lógica compleja es difícil de implementar. | Útil si necesitamos compartir reglas con el equipo de Frontend. |

---

## 2. Documentación del "Caso Propio" (Caso #6)

Además de los errores propuestos por la IA, he implementado una validación de seguridad crítica: **Detección de Campos Desconocidos**.

* **El Ataque:** Un usuario malintencionado envía campos extra en el JSON (ej. `"es_admin": true` o `"precio_descuento": 99`) esperando que la base de datos los guarde ciegamente y altere la lógica del sistema (Mass Assignment Vulnerability).
* **La Defensa:** Mi función `validar_producto_ecomarket` compara las llaves recibidas contra la lista blanca de campos permitidos. Si encuentra alguna llave extra, rechaza la petición inmediatamente.

```python
# Fragmento de código implementado
campos_extra = set(data.keys()) - set(campos_requeridos)
if campos_extra:
    return False, f"Seguridad: Se detectaron campos desconocidos: {campos_extra}"