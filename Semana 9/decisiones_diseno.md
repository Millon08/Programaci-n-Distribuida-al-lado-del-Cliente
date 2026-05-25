# Decisiones de Diseño - Circuit Breaker

## 1. Justificación de Umbrales
- **umbral_fallos = 3**: Un valor bajo protege rápido al servidor. Se eligió 3 porque 1 o 2 fallos pueden ser problemas transitorios normales (ruido de red). 3 fallos consecutivos en menos del tiempo del timeout sugieren un problema real en EcoMarket.
- **timeout_reset = 10 segundos**: Es un tiempo prudente para esperar que un pod o microservicio se reinicie o escale. Un valor menor causaría flapeo constante.

## 2. Límites del Circuit Breaker
- **¿Qué NO resuelve?**: El Circuit Breaker protege los recursos y evita agravar caídas, pero no recupera magicamente el servicio. Tampoco reemplaza al mecanismo de retries (de hecho, el retry no debe intentar si el breaker está abierto). No soluciona problemas lógicos como bugs de código (errores 500 consistentes por payload inválido), solo mitigará la carga de esos bugs.

## 3. Escenario 2: Respuestas Lentas
- **Decisión**: Sí, los timeouts (respuestas lentas) DEBEN activar el breaker. 
- **Implementación**: En la función `_es_fallo_servidor`, capturamos explícitamente `TimeoutError` o revisamos la latencia. Si el cliente tiene un timeout configurado en su HTTP client (ej. 5 segundos), este lanzará un error que el breaker interpretará como equivalente a un 503.
