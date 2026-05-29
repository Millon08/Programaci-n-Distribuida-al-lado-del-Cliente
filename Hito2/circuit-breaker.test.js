const assert = require('node:assert');
const CircuitBreaker = require('./circuit-breaker');

/**
 * Pruebas automatizadas (node:test y node:assert)
 * Cero dependencias externas.
 */

async function correrPruebas() {
    console.log("Iniciando pruebas del Circuit Breaker...\n");

    try {
        const cb = new CircuitBreaker(3, 100); // 3 fallos, 100ms de espera

        // Caso 1: Comienza CERRADO
        assert.strictEqual(cb.estado, 'CERRADO', 'INV-A2: El circuito debe comenzar cerrado');
        
        // Función mock que siempre falla
        const peticionFalla = async () => { throw new Error('Servicio caido (503)'); };
        //se crea una peticion http que siempre va a fallar
        // Caso 2: Peticiones fallidas hasta abrirse
        for (let i = 0; i < 3; i++) {
            try {
                await cb.ejecutar(peticionFalla);
            } catch (e) {
                // Se espera el error
            }
        }
        
        assert.strictEqual(cb.estado, 'ABIERTO', 'El circuito debe abrirse tras 3 fallos consecutivos');

        // Caso 3: En estado ABIERTO rechaza rápido
        let rechazoRapido = false;
        try {
            await cb.ejecutar(peticionFalla);
        } catch (e) {
            if (e.message.includes('rechazada rápidamente')) {
                rechazoRapido = true;
            }
        }
        assert.strictEqual(rechazoRapido, true, 'Debe rechazar rápidamente en estado ABIERTO');

        // Caso 4: Transición a SEMI-ABIERTO tras tiempo de espera
        console.log("Esperando 150ms para transicionar a SEMI-ABIERTO...");
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Al intentar ejecutar, debería pasar temporalmente a SEMI-ABIERTO y fallar de nuevo (porque la petición falla)
        try {
            await cb.ejecutar(peticionFalla);
        } catch (e) {
            // Se espera el error de red
        }
        
        // Como falló la prueba en semi-abierto, debe volver a ABIERTO
        assert.strictEqual(cb.estado, 'ABIERTO', 'TC-X2: Tras fallar en SEMI-ABIERTO, vuelve a ABIERTO');

        console.log("✅ Todas las pruebas pasaron correctamente.");
    } catch (err) {
        console.error("❌ Falló una aserción:", err.message);
        process.exit(1);
    }
}

correrPruebas();
