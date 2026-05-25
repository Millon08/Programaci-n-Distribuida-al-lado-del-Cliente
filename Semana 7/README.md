# Decisiones de Diseño (Reto 1) - Cliente SSE Multiplex

## 1. ¿Por qué usar una única conexión multiplexada en lugar de múltiples conexiones?
**Respuesta:** En EcoMarket necesitamos escuchar eventos de precios, inventario, pedidos y alertas. Si abrimos una conexión SSE por cada módulo, estaríamos ocupando múltiples descriptores de red y recursos tanto en el cliente como en el servidor (un navegador típicamente limita a 6 conexiones por dominio). Una única conexión multiplexada ahorra recursos y previene agotar el límite de conexiones del navegador/cliente.

## 2. ¿Cómo diferencia el cliente qué dato pertenece a qué módulo?
**Respuesta:** Dado que todo llega por el mismo "tubo" (stream), cada evento SSE debe incluir una etiqueta o campo (como `event: tipo_evento` o un campo `tipo` dentro del JSON). El cliente usa un `EventRouter` que inspecciona este tipo y delega el mensaje al handler correspondiente.

## 3. ¿Qué ocurre si un módulo es más lento procesando que otros?
**Respuesta:** Si el procesamiento de eventos es bloqueante, un handler lento (ej. guardar un pedido en BD) retrasará el procesamiento de todos los demás eventos entrantes, causando que los búferes de red se llenen. Por esto, los handlers deben ser asíncronos y no bloquear el bucle principal que lee el stream.

## 4. ¿Qué debe hacer el cliente si la conexión se cae?
**Respuesta:** El cliente debe detectar la desconexión e intentar reconectar de manera automática (auto-reconnect), pero utilizando un *backoff exponencial* con *jitter* para no tumbar al servidor si miles de clientes se desconectan a la vez e intentan reconectar en el mismo milisegundo.

## Síntesis Correctiva
Originalmente podía pensarse que el cliente simplemente abre la conexión y ya. Sin embargo, del lado del cliente la responsabilidad es inmensa: debemos parsear el flujo continuo, lidiar con JSONs rotos o eventos desconocidos sin que la aplicación crashee, y enrutar inteligentemente.

---

# Reto 5 (Profundiza) - Routing con Prioridades

## ¿Por qué elegí Herencia para EventRouterPrioritizado?
He decidido usar herencia (creando una clase `EventRouterPrioritizado` que hereda de `EventRouter`) porque el enrutamiento con prioridades modifica la naturaleza intrínseca de cómo el router despacha los mensajes a nivel interno. Un decorador envuelve la llamada pero no puede alterar la cola interna de mensajes no procesados de manera sencilla si el stream se congestiona. Al heredar, puedo sobreescribir el método interno de procesamiento (o añadir una cola de prioridad basada en `heapq`) manteniendo la misma interfaz pública de `register_handler` y `route_event`.
