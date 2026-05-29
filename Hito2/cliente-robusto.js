const CircuitBreaker = require('./circuit-breaker');
const TokenManager = require('./token-manager');

/**
 * Cliente Robusto - Integración de Circuit Breaker y Token Manager
 * Implementado como una receta lineal usando async/await.
 */
class ClienteRobusto {
    constructor() {
        this.tokenManager = new TokenManager();
        this.circuitBreaker = new CircuitBreaker(3, 5000); // 3 fallos, 5 seg de espera
    }

    /**
     * Orquesta la petición:
     * 1. Solicita el permiso (Token).
     * 2. Envía la petición protegida por el escudo (Circuit Breaker).
     */
    async hacerPeticion(peticionSimulada) {
        // PASO 1: Obtener o refrescar el token
        const token = await this.tokenManager.getToken();//Antes de siquiera mirar el servidor, el cliente frena y dice: "Necesito mi pase de acceso".
        
        // PASO 2: Ejecutar la petición protegiéndola con el Circuit Breaker
        // Pasamos el token a la petición simulada
        const resultado = await this.circuitBreaker.ejecutar(peticionSimulada, token);
        
        return resultado;
    }
}

module.exports = ClienteRobusto;
