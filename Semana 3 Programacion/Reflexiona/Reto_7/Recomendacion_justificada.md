Reto 7: Analista de Trade-offs de Concurrencia

## 1. Archivo generado: `comparacion_coordinacion.py`
Se desarrolló y entregó el archivo `.py` que testea limpiamente los 4 flujos en el *Event Loop* bajo el siguiente escenario propuesto:
**`productos=200ms` | `categorías=100ms` | `perfil=500ms` | `notificaciones=TIMEOUT/Error a los 2s`**

## 2. Análisis Crítico por Estrategia
Criterios explicativos para las preguntas clave evaluadas en el código:
* **¿Cuándo se muestra el primer dato al usuario?** Con `gather()` hasta que TODO acaba (~2-10s si falla al final). Con `as_completed` o `wait(FIRST_COMPLETED)` al instantáneo **rápido tiempo de la primera en terminar** (`100ms` para Categorías).
* **¿Qué pasa cuando 1 de 4 falla?** Con `gather(..., return_exceptions=False)`, interrumpe limpiamente y estalla un error generalizado. Con modos asíncronos `wait`, lo capturas individual y prosigues.
* **¿Qué pasa si una vuela y dura 10s?** Bloquea los displays integrales como `gather()` reteniendo tu UX en blanco; en las versiones iteradas `wait() / as_completed()`, todo lo demás llega antes de manera libre.
* **¿Es fácil agregar una 5ta petición?** Extremo fácil en todas (solo añadirla a la lista de "Tareas o SETs").
* **¿Código extra generado?** `gather()` usa 1 sola línea; `wait(FIRST_COMPLETED)` requiere un bloque `while pending:`.


## 3. Tabla Comparativa de Calificación (De 1 a 5, 5 = Excelente)

| Estrategia  | Latencia Percibida del UX | Robustez a Fallos Ciegos | Simplicidad / Complejidad | Escalado / Mantenibilidad |
|---|---|---|---|---|
| **`asyncio.gather()`** | ⭐ (Lenta si hay retrasos) | ⭐⭐ (Sensible al fallo grupal) | ⭐⭐⭐⭐⭐ (Una línea limpia)| ⭐⭐⭐⭐⭐ (Solo agrupa) |
| **`asyncio.wait(FIRST_COMPLETED)`** | ⭐⭐⭐⭐⭐ (Inmediato) | ⭐⭐⭐⭐ (Precisa)  | ⭐⭐ (Requiere `while` state loops)  | ⭐⭐⭐⭐ (Maneja dependencias conjuntas) |
| **`asyncio.as_completed()`** | ⭐⭐⭐⭐⭐ (Inmediato) | ⭐⭐⭐⭐ (Controlado en for) | ⭐⭐⭐⭐ (Solo un for simple)  | ⭐⭐⭐ (Poco control de prioridades) |
| **`asyncio.wait(FIRST_EXCEPTION)`** | ⭐ (Depende de fallos rápidos) | ⭐⭐⭐⭐⭐ (Aborto inteligente) | ⭐⭐⭐ (Bloques de deshabilitar sobrantes)| ⭐⭐⭐⭐ (Excelente proxy transaccional)|

---

## 4. Diagrama Temporal Comparativo 

### Con `asyncio.gather()` (Penosamente Lento si Algo Secundario Cuelga)
```text
0ms:   [Disparo]: Lanza (Productos, Categorias, Perfil, Notificaciones) a la red.
100ms: [Categorías] finaliza. Se queda en RAM atascada... esperando al jefe.
200ms: [Productos] finaliza. Se queda en RAM atascada...
500ms: [Perfil] finaliza. Se queda en RAM...
... el UX de la app esta en "Loading spinner" ...
2000ms: [Notificaciones] ¡Falla por Timeout!.
-> ¡Excepción! Todo lo cargado se destruye, el gather avienta el error a principal. Pantalla de colapso en UI.
```

### Con `asyncio.as_completed()` o `asyncio.wait(FIRST_COMPLETED)` (Reactivo / UX Moderno)
```text
0ms:   [Disparo]: Lanza las 4 a la red.
100ms: [Categorías] finaliza. -> 🎨 EL NAVEGADOR DIBUJA CATEGORIAS AL USUARIO. 
200ms: [Productos] finaliza. -> 🎨 EL UI METE LOS PRODUCTOS. ¡EL CLIENTE YA COMPRA!
500ms: [Perfil] finaliza. -> 🎨 CARGA LA FOTO DEL CLIENTE TARDÍA.
... el usuario ya está usando la app felizmente por 1.5s ...
2000ms: [Notificaciones] Arroja EXCEPCION. -> El bloqué try/except del `While loop` pinta el icono rojo en la campanita de la UI, pero nadie se estresó ni vio colgarse la app.
```

---

## 5. Recomendación Específica para EcoMarket 🛒

La estrategia elegida por justificación es: **`asyncio.wait(return_when=asyncio.FIRST_COMPLETED)`**.

**Justificación:** EcoMarket necesita construir un **Dashboard**. Un dashboard no es una transacción bancaria ACID obligatoriamente ligada al "todo sube firme, o nada sube". Es fundamentalmente una amalgama de widgets informativos (`perfil`, `catalogo`, `notificaciones`, `inventario`).
Usando `wait(FIRST_COMPLETED)` adquirimos la invaluable bendición de ir inyectando resultados de bases de datos lejanas al cliente *en tiempo real según aterricen* (UX Dinámico). Posee además una inmensa ventaja técnica por sobre `as_completed`: nos permite gestionar grupos y "tareas pendientes (`pending`), permitiéndome usar mi rutina de validación de **Tareas Críticas** del Reto 4 (verificar si 'productos' y 'perfil' ya llegaron para dar luz verde). `as_completed` me entregaba un "futuro ciego en un loop", pero `wait()` controla estados precisos y nombres exactos. Simplemente el mejor controlador de flotas para vistas al usuario.
