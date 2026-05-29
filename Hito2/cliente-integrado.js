const ClienteRobusto = require('./cliente-robusto');

/**
 * Entregable del Reto 4: Cliente Integrado
 * Demostración de las 3 fases del circuito usando un mock simple.
 */

// Contador global para nuestro mock interno
let contadorPeticionesMock = 0;//es la "memoria" del servidor falso
//como vamos a realizar 10 peticiones seguidas el servidor falso necesita saber en cual va para saber si toca fallar
/**
 * Simula una petición HTTP de forma predecible.
 * Si el contador es < 3, falla con 503. Si no, tiene éxito.
 */
async function simularPeticionHTTP(token) {//el programa al inentar entrar a internet entra a esta funcion
    contadorPeticionesMock++;//le suma uno al contador
    console.log(`      [Mock Network] Recibiendo petición con token: ${token.substring(0, 10)}...`);
    //imprime en pantalla que recibio el intento
    // Simulamos latencia
    await new Promise(resolve => setTimeout(resolve, 50));//pausa el codigo por 50 mls 
    //finge que los datos estan pasando por un cable fisico
    if (contadorPeticionesMock <= 3) {//si es la peticion 1,2 o 3 el servidor falso lanza un error 503
        throw new Error('503 Service Unavailable');
    }
    //a partir de la peticion 4 en adelante deja de lanzar errores y devuelve los datos con exito
    return { data: 'Respuesta exitosa de la API', status: 200 };
}

// Función principal para demostrar el comportamiento
async function ejecutarDemo() {
    console.log("=== INICIANDO DEMO DE RESILIENCIA (10 PETICIONES) ===");
    
    // Aquí configuramos un tiempo corto para no hacer la demo aburrida (1.5 segundos en vez de 5)
    const cliente = new ClienteRobusto();//crea el cliente principal
    cliente.circuitBreaker.tiempoEsperaMs = 1500; 
    
    for (let i = 1; i <= 10; i++) {//bucle que se repite 10 veces
        console.log(`\n--- Petición ${i} --- [Estado del CB: ${cliente.circuitBreaker.estado}]`);
        try {//en esta parte se envia al cliente a 
            const respuesta = await cliente.hacerPeticion(simularPeticionHTTP);
            console.log(`   ✅ ÉXITO: ${respuesta.data} (CB Estado: ${cliente.circuitBreaker.estado})`);
        } catch (error) {
            console.log(`   ❌ ERROR: ${error.message} (CB Estado: ${cliente.circuitBreaker.estado})`);
        }

        // Para la petición 4, esperamos a que pase el tiempo de expiración del Circuit Breaker
        // para poder ver el estado SEMI-ABIERTO en la petición 5.
        if (i === 4) {
            console.log("\n   ⏳ Esperando 1.6 segundos para que el circuito pase a Semi-Abierto...");
            await new Promise(resolve => setTimeout(resolve, 1600));
        }
    }
    
    console.log("\n=== FIN DE LA DEMO ===");
}

ejecutarDemo();
