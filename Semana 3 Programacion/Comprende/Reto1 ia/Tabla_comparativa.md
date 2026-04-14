Tabla Comparativa de Modelos

| Modelo | Complejidad Cognitiva / Código | Tiempo Ejecución (simulado 500ms c/u) | ¿Usa Hilos OS? | Soporte p/ Retoques individual de Excepciones |
|--------|----------------|----------------|----------------|----------------|
| **Síncrono (Base)** | Muy Bajo | ~1.500s | Bloquea 1 Hilo | Si, uno tras otro interrumpe flujo |
| **Callbacks** | Alto (Callback Hell) | ~0.505s | Sí (varios hilos) | Aislado, muy difícil de coordinar en conjunto |
| **Futures** | Medio | ~0.505s | Sí (varios hilos) | Capturas estables en ciclo `as_completed` |
| **Async/Await** | Bajo (Sintaxis amigable) | ~0.502s | **No** (Event loop en 1 hilo) | Perfecto con `gather(..., return_exceptions=True)`|
