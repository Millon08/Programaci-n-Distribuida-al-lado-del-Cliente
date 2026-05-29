/**
 * Token Manager - Archivo de la Semana 8 (bugs corregidos)
 * Se encarga de simular la obtención y validación de un token JWT.
 */
class TokenManager {
    constructor() {//variables que actuan como cache interno para no dar una vuelta por la token en internet
        this.tokenActual = null;
        this.tiempoExpiracion = null;
    }

    /**
     * Simula la obtención inicial de un token.
     */
    async login() {
        // Simulamos un retraso de red
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Simula un token válido por 30 minutos
        this.tokenActual = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_payload';//"Genera" un string que parece un token JWT real
        this.tiempoExpiracion = Date.now() + (30 * 60 * 1000); //Toma la hora actual (Date.now()) y le suma 30 minutos convertidos a milisegundos.
        
        return this.tokenActual;
    }

    /**
     * Verifica si el token es válido o necesita ser refrescado.
     */
    async getToken() {
        if (!this.tokenActual) {//llama a la función login(), si es la primera vez que se corre el programa para que consiga y guarde una token
            // Bug corregido: si no hay token, hacer login inicialmente
            return await this.login();
        }

        // Bug corregido: Lógica correcta para detectar expiración
        const expirado = Date.now() > this.tiempoExpiracion;//se revisa la caducidad del toke,si ya caduco llama a this.refresh()
        if (expirado) {
            return await this.refresh();
        }

        return this.tokenActual;//Si pasó los dos filtros anteriores (sí hay token y no ha caducado), simplemente te devuelve
        //  el que ya tiene guardado en el caché de la memoria RAM.
    }

    /**
     * Simula la lógica de refresh token.
     */
    async refresh() {
        await new Promise(resolve => setTimeout(resolve, 100));
        this.tokenActual = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_refreshed_payload';//sobreescribe la credencial vieja que estaba guardada en el cache
        this.tiempoExpiracion = Date.now() + (30 * 60 * 1000); //le da nueva caducidad
        return this.tokenActual;//la entrega
    }
}

module.exports = TokenManager;
