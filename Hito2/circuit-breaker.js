/**
 * Implementación del Circuit Breaker usando lógica simple de fechas.
 * Decisiones de diseño:
 * - Se usa Date.now() para calcular el tiempo transcurrido en estado ABIERTO.
 * - Cero dependencias externas y sin timers complejos (no setInterval/setTimeout).
 * - Facilita la comprensión y el testing sincrónico.
 */
class CircuitBreaker {
    constructor(umbralFallos = 3, tiempoEsperaMs = 5000) {
        this.umbralFallos = umbralFallos;//toma los numeros que entraron a la funcion y los guarda con this.
        this.tiempoEsperaMs = tiempoEsperaMs;
        
        this.estado = 'CERRADO';//el estado inicia como cerrado porque el servicio esta iniciando y no ha fallado
        this.fallosConsecutivos = 0;//Permite que el regristrardor de fallo empiece a sumar desde 0
        this.tiempoFallo = null; // Guarda la marca de tiempo de cuando el circuito se abrió
    }

    /**
     * Evalúa si debe permitir la petición actual según el estado y el tiempo transcurrido.
     */
    puedeEjecutar() {
        if (this.estado === 'CERRADO') {//si el puente esta sano deja pasar la peticion devolviendo true
            return true;
        }

        if (this.estado === 'ABIERTO') { //El puete esta roto,cuando llega una peticion queriendo pasar se hace un calculo
            const tiempoTranscurrido = Date.now() - this.tiempoFallo;//Se resta la hora actual "date" por la hora en la que sucedio el fallo
            if (tiempoTranscurrido > this.tiempoEsperaMs) {
                // Ha pasado el tiempo, pasamos a semi-abierto para probar
                this.estado = 'SEMI-ABIERTO';//Si el tiempo de espera ya se cumplio,se cambia de estado a Semi-abierto y solo deja pasar una peticion 
                return true;//para ver si el servicio ya se recupero
            }
            return false;//si no se ha cumplido el tiempo de espera,el estado sigue abierto esperando a que se recupere el servicio
        }

        if (this.estado === 'SEMI-ABIERTO') {
            // Ya hay una petición de prueba en curso
            return false;//si llega otra peticion se bloquea porque se esta procesando la anterior para ver si ya se recupero el servicio
        }

        return false;//bloquea la peticion al momento de que ocurra un error raro en el que el estado no se encuentre en cerrado,abierto o semi-abierto
    }

    registrarExito() {
        // En cualquier estado que no sea cerrado, un éxito lo resetea
        this.estado = 'CERRADO';//si ahy exito en el estado semi-abierto el sistema vuelve a cerrado
        this.fallosConsecutivos = 0;//se reinician los contenedores para que las peticiones vuelvan a pasar
        this.tiempoFallo = null;
    }

    registrarFallo() {
        if (this.estado === 'SEMI-ABIERTO') {
            // Si falla la prueba en semi-abierto, se vuelve a abrir inmediatamente
            this.estado = 'ABIERTO';
            this.tiempoFallo = Date.now();//se reinicia el cronometro de espera 
        } else {
            // En estado cerrado, acumulamos fallos
            this.fallosConsecutivos++;//ocurre un error y es guardado aqui
            if (this.fallosConsecutivos >= this.umbralFallos) {//se revisa si los fallos igualan o superan el umbral
                this.estado = 'ABIERTO';//si si lo igualan o superan se cambia al estado abierto
                this.tiempoFallo = Date.now();//se anota la hora del error
            }
        }
    }

    /**
     * Envuelve una promesa (función asíncrona) para protegerla.
     */
    async ejecutar(funcionPeticion, ...args) {//recibe la peticion que quieras hacer y cualquier dato que esa peticion necesite
        if (!this.puedeEjecutar()) {//antes de siquiera conectarse a internet revisa en que estado esta el puente,si esta abierto se lanza un error instantaneo
            throw new Error(`CircuitBreaker en estado ${this.estado}: Petición rechazada rápidamente.`);
        }

        try {//si el estado era optimo ,el codigo entra al bloque try 
            const resultado = await funcionPeticion(...args);//se ejecuta la llama a internet await 
            this.registrarExito();//si el servidor responde bien y entrega los datos,los guarda en resultados
            return resultado;//y le avisa a registrarExito que todo salio bien
        } catch (error) {//si algo sale mal dentro de try 
            this.registrarFallo();//se registra el error
            throw error;//se lanza el mensaje de error para que la aplicacion sepa que fallo
        }
    }
}

module.exports = CircuitBreaker;
