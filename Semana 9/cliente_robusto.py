import time
import logging
import sys
import os

# Agregamos la ruta de semana 8 para importar TokenManager (simulando integración real)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'semana 8 antiG'))

from circuit_breaker import CircuitBreaker
try:
    from token_manager import TokenManager
except ImportError:
    # Fallback mock si no se puede importar
    class TokenManager:
        def __init__(self): pass
        def get_valid_token(self): return "mock_token"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class ClienteRobusto:
    def __init__(self):
        self.breaker = CircuitBreaker(umbral_fallos=3, timeout_reset=5)
        self.tm = TokenManager()
        self.modo_falla = False

    def set_modo_falla(self, activo):
        self.modo_falla = activo

    def _simular_peticion_red(self, url, token):
        # NOTA: En un caso real, el interceptor 401 correría ANTES del breaker,
        # o el breaker simplemente lo ignoraría porque _es_fallo_servidor() devuelve False para 401.
        if self.modo_falla:
            raise Exception("503 Service Unavailable")
        return f"Respuesta exitosa de {url}"

    def hacer_peticion(self, url):
        token = self.tm.get_valid_token()
        
        # Envolvemos la petición en el breaker
        # OJO con el Deadlock Auth-Breaker: un error 401 NUNCA debe abrir este breaker!
        try:
            res = self.breaker.call(self._simular_peticion_red, url, token)
            logging.info(f"[ClienteRobusto] -> {res}")
            return res
        except Exception as e:
            logging.error(f"[ClienteRobusto] -> Error: {e}")
            return None

def main():
    cliente = ClienteRobusto()
    
    logging.info("--- 1. MODO NORMAL (3 peticiones exitosas) ---")
    for _ in range(3):
        cliente.hacer_peticion("/api/datos")
        time.sleep(0.5)
        
    logging.info("--- 2. ACTIVA MODO FALLO 503 ---")
    cliente.set_modo_falla(True)
    for _ in range(4): # 3 para abrir, 1 para ser rechazado inmediato
        cliente.hacer_peticion("/api/datos")
        time.sleep(0.5)

    logging.info("--- 3. ESPERA TIMEOUT (Estado Semiabierto) ---")
    logging.info("Durmiendo 6 segundos para pasar el timeout_reset del breaker...")
    time.sleep(6)
    
    logging.info("--- 4. RESTAURA MODO NORMAL (Recuperación) ---")
    cliente.set_modo_falla(False)
    # Esta petición es la de prueba (Semiabierto -> Cerrado)
    cliente.hacer_peticion("/api/datos")
    
    # Esta petición ya entra en estado Cerrado
    cliente.hacer_peticion("/api/datos")

if __name__ == "__main__":
    with open("demo_resiliencia.log", "w") as f:
        # Redirigir stdout a demo_resiliencia.log para el entregable
        sys.stdout = f
        main()
        sys.stdout = sys.__stdout__
    logging.info("Demo completada. Se generó demo_resiliencia.log")
    main() # Correr también en terminal
