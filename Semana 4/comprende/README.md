# Semana 4: Patrones de Comunicación — Polling y Suscripción a Eventos

## Reto 1: Traza mental del ciclo de polling

### 🍕 La analogía: Llamando a la pizzería
Imagina que estás organizando una reunión y llamas a tu pizzería favorita (el servidor) para saber si ya actualizaron sus promociones del día.

1. **Primera llamada:** "Hola, ¿me das las promociones?" El de la pizzería te lee toda la lista de pizzas y te dice: "Esta es la promoción versión `abc123`". Anotas todo.
2. **Segunda llamada (5 min después):** Para no hacerle perder el tiempo (y ahorrar tu saldo), ahora eres más inteligente y preguntas: "Oye, ¿tienes algo más nuevo que la versión `abc123`?". El de la pizzería revisa y dice: "No, todo sigue igual". Como no cambió nada, no te vuelve a leer todo el menú, y la llamada es cortísima.
3. **Tercera llamada (otros 5 min después):** Vuelves a preguntar por algo más nuevo que `abc123`. La respuesta es la misma: "No, todo igual". Como ves que no cambian el menú muy seguido, decides que la próxima vez vas a esperar un poco más antes de volver a llamar.
4. **Cuarta llamada:** "Oye, ¿algo más nuevo que `abc123`?". "¡Sí! Acabamos de poner una nueva promo. Te leo la nueva lista... Esta es la versión `def456`". Vuelves a anotar todo y sabes que tu próxima llamada preguntará por la versión `def456`.

---

### 📊 Traza del ciclo de Short Polling en EcoMarket

| Tiempo | Consulta | 1. Headers del cliente | 2. Status del Servidor | 3. Transferencia de Datos | 4. ¿Qué hace el cliente? | 5. Ajuste de intervalo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `t=0s` | **#1** | `GET /api/productos`<br>*(Sin If-None-Match)* | `200 OK`<br>`ETag: "abc123"` | **Completa:** Payload pesado con todos los datos JSON. | Guarda el ETag `"abc123"`, notifica a la UI y muestra los datos. | Se mantiene en **5s** (intervalo base). |
| `t=5s` | **#2** | `GET /api/productos`<br>`If-None-Match: "abc123"` | `304 Not Modified`<br>*(No hay cambios)* | **Vacía (0 bytes de payload):** Solo viajan los headers HTTP. | Al ver el 304, no hace nada; la UI se mantiene intacta. | Crece (ej. a **7.5s** o **10s**) para no saturar al servidor. |
| `t=15s` | **#3** | `GET /api/productos`<br>`If-None-Match: "abc123"` | `304 Not Modified`<br>*(No hay cambios)* | **Vacía (0 bytes de payload):** Solo viajan los headers HTTP. | Sigue sin hacer nada con los datos. | Crece aún más (ej. a **15s** o **20s**), aplicando *backoff*. |
| `t=35s` | **#4** | `GET /api/productos`<br>`If-None-Match: "abc123"` | `200 OK`<br>`ETag: "def456"` | **Completa:** Payload pesado con la nueva lista actualizada. | Notifica los nuevos datos a la UI y actualiza su ETag a `"def456"`. | Se **resetea a 5s** (intervalo base) porque hubo actividad. |

<br>

### 💡 ¿Por qué ETag es más eficiente que comparar datos completos?
El uso del header `ETag` permite que el servidor evalúe rápidamente si la información cambió antes de tener que construir y enviar toda la respuesta. Si el ETag coincide, el servidor responde con un código `304 Not Modified` y un cuerpo vacío. Esto ahorra ancho de banda en la red, esfuerzo de CPU en el servidor (que no serializa los datos) y en el cliente (que no tiene que parsear el JSON de nuevo).
