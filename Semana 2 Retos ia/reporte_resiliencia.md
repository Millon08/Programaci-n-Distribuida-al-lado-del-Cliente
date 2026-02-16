# 🛡️ Estrategia de Resiliencia y Idempotencia

**Ingeniero:** [Tu Nombre]
**Componente:** Middleware de Reintentos (Retry)

## 1. Diseño del Algoritmo
Se implementó un mecanismo de **Exponential Backoff con Jitter** para manejar fallos transitorios.

* **¿Por qué Exponential Backoff?**
    Si un servidor está caído por sobrecarga, bombardearlo con reintentos inmediatos solo empeorará el problema. Esperar tiempos crecientes (1s, 2s, 4s, 8s...) da tiempo al servidor para recuperarse ("enfriarse").
* **¿Por qué Jitter (Variación Aleatoria)?**
    Si 1000 clientes fallan al mismo tiempo y todos esperan exactamente 2 segundos, volverán a golpear al servidor juntos (Thundering Herd Problem), tirándolo de nuevo. El Jitter desincroniza a los clientes.

## 2. Análisis de Idempotencia: ¿Cuándo es seguro reintentar?

La **Idempotencia** significa que ejecutar una operación varias veces tiene el mismo efecto que ejecutarla una sola vez.

### ✅ Casos Seguros para Reintentar (Idempotentes)
* **GET (Lectura):** Leer un producto 10 veces no cambia nada en el servidor. Es seguro usar `@with_retry`.
* **PUT (Reemplazo):** Si subo un archivo "foto.jpg" 5 veces, el resultado final es el mismo (la foto está ahí). Es seguro.
* **DELETE (Borrado):** Borrar algo que ya está borrado suele dar 404, pero no rompe nada. Es relativamente seguro.

### ⚠️ Casos PELIGROSOS (No Idempotentes)
* **POST (Creación):**
    * *Escenario:* Envío una orden de compra -> El servidor cobra la tarjeta -> Se corta internet antes de recibir el "OK".
    * *Riesgo:* Si mi cliente reintenta automáticamente, podría **cobrar la tarjeta dos veces** (crear dos órdenes).
    * *Solución:* Nunca poner reintentos automáticos en `POST` a menos que el servidor soporte "Idempotency Keys" (un ID único por transacción).

## 3. Conclusión
El decorador `@with_retry` se ha integrado en las funciones de lectura (`obtener_producto`, `listar_productos`). Para las funciones de escritura (`crear_producto`), se ha decidido mantener el fallo inmediato para evitar duplicidad de datos hasta implementar claves de idempotencia en el backend.