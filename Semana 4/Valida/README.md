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

---

## Reto 5 (Bono): Diseño de Migración a WebSocket

### 1. Interfaz Común Propuesta (Contrato del Cliente)
Para que los observadores no se den cuenta de que cambiamos el motor por debajo (de Polling a WebSocket), la nueva clase `ServicioWebSocket` debe heredar de `Observable` y mantener exactamente esta misma interfaz pública:
* `iniciar()`: En lugar de arrancar el bucle HTTP iterativo, abre la conexión `ws://`.
* `detener()`: En lugar de apagar el bucle y la bandera, envía una señal de cierre de socket limpia (`close()`).
* `suscribir(evento, callback)`: Queda exactamente igual (heredado).
* `desuscribir(evento, callback)`: Queda exactamente igual (heredado).

### 2. Diagrama de Estados del Cliente WebSocket
A diferencia del polling donde el estado es solo "activo/inactivo" (cada ciclo HTTP nace y muere rápido), WebSocket requiere que gestionemos la persistencia de la conexión:

```text
[ Desconectado ] 
       │ (llaman a iniciar)
       ▼
[ Conectando... ] ◄────────┐ (Intento de reconexión auto)
       │ (éxito)           │
       ▼                   │ (se corta internet/red)
[ Conectado ] ─────────────┘
       │ (falla reconexión > N veces)
       ▼
[ Degradado ] (Se enciende un Polling de respaldo temporal)
```

### 3. Impacto en el Código Cliente (Qué cambia y qué NO cambia)

**✅ Lo que NO cambiaría (gracias al Patrón Observer):**
- **Cero cambios** en las funciones de la Interfaz Gráfica (`actualizar_ui`).
- **Cero cambios** en los sistemas de alerta (`verificar_stock`).
- **Cero cambios** en el manejo de logs y errores visuales. Todos los consumidores de la información siguen esperando un evento de string como `"datos_actualizados"`, sin importar de qué tecnología de red provienen.

**⚠️ Lo que SÍ cambiaría (Lógica interna del nuevo ServicioWebSocket):**
- **Manejo de conexión:** Hay que escribir lógica para escuchar cuando el socket se cierra de repente (`onclose` / `onerror`) que no existía en peticiones HTTP individuales.
- **Heartbeats (Pings):** El cliente probablemente necesite enviar un ping recurrente para asegurar al servidor "sigo vivo" e identificar "conexiones zombis".
- **Cola de mensajes pendientes:** Si un usuario hace una acción mientras la red parpadea y el socket está intentando reconectar, el cliente debe encolar esa acción en un buffer temporal para mandarla tan pronto recupere la conexión.
