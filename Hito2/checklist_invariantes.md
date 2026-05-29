# Checklist de Invariantes (Reto 7)

- [x] **INV-A1 (El estado inicial del Circuit Breaker siempre es CERRADO)**: 
      *Evidencia/Estado*: Cumplido. En `circuit-breaker.js`, el constructor define explícitamente `this.estado = 'CERRADO'`. Está validado en el Caso 1 de `circuit-breaker.test.js`.

- [x] **INV-A2 (En estado SEMI-ABIERTO, solo se permite pasar una petición de prueba)**: 
      *Evidencia/Estado*: Cumplido. En `circuit-breaker.js`, dentro del método `puedeEjecutar()`, si el estado es `SEMI-ABIERTO`, cualquier petición adicional es rechazada inmediatamente devolviendo `false`.

- [x] **INV-B1 (Los contadores de errores son locales para cada instancia)**: 
      *Evidencia/Estado*: Cumplido. En `circuit-breaker.js`, el contador `this.fallosConsecutivos` está asignado al objeto (`this`), garantizando que múltiples circuitos no compartan fallos.

- [x] **INV-B2 (Un error de autenticación 401 NO debe abrir el circuito)**: 
      *Evidencia/Estado*: Cumplido. En la receta de `cliente-robusto.js`, la validación de tokens ocurre antes. Los errores 401 son resueltos por el `TokenManager` y no llegan a registrarse como fallos de red en el circuito.

- [x] **INV-B3 (Una petición exitosa en estado SEMI-ABIERTO resetea el circuito a CERRADO)**: 
      *Evidencia/Estado*: Cumplido. En `circuit-breaker.js`, si la promesa tiene éxito en `ejecutar()`, se llama a `registrarExito()`, lo cual cambia el estado a `CERRADO` y pone los fallos en 0.

- [x] **TC-X1 (El TokenManager realiza un Login inicial automático si no existe token)**: 
      *Evidencia/Estado*: Cumplido. En `token-manager.js`, el método `getToken()` incluye la validación: `if (!this.tokenActual) { return await this.login(); }`, asegurando las credenciales.

- [x] **TC-X2 (Si falla la petición de prueba en SEMI-ABIERTO, el circuito vuelve a ABIERTO)**: 
      *Evidencia/Estado*: Cumplido. En el método `registrarFallo()`, si el estado es `SEMI-ABIERTO`, este regresa instantáneamente a `ABIERTO` y se actualiza `this.tiempoFallo`. Validado en el Caso 4 de las pruebas.
