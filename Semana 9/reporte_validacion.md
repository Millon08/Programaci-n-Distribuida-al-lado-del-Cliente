# Reporte de Validación - Semana 9 (Circuit Breaker)

| Caso de Prueba | Estado Esperado | Estado Observado |
|---|---|---|
| 1. Petición normal | Éxito | Éxito |
| 2. Petición con 401 | Falla (no abre) | Falla (no abre) |
| 3. Múltiples fallas 503 | Abre circuito | Abre circuito |
| 4. Timeout espera red | Cuenta como 503 | Cuenta como 503 |
| 5. Petición mientras abierto | Rechazo Inmediato | Rechazo Inmediato |
| 6. Fin de timeout_reset | Pasa a Semiabierto | Pasa a Semiabierto |
| 7. Falla en Semiabierto | Vuelve a Abierto | Vuelve a Abierto |

## Evidencia de Protección al Servidor
- Peticiones que llegaron al servidor ANTES de abrir: 3
- Peticiones que llegaron al servidor MIENTRAS estaba abierto (simulación 10 iteraciones): 0
- Rechazos inmediatos en el cliente ahorrando viajes de red: 10

## Bugs Documentados
- **Bug**: El contador de fallos no se reseteaba a 0 al pasar de SEMIABIERTO a CERRADO tras un éxito. Esto causaba que un solo fallo posterior volviera a abrir el circuito inmediatamente.
- **Fix**: Se agregó `self._fallos_consecutivos = 0` en el método `registrar_exito()`.
