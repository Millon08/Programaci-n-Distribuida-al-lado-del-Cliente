import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CircuitBreaker:
    """
    Decisiones de Diseño - CircuitBreaker
    =====================================
    - Reto 1: Estado almacenado en memoria de la clase para proteger servicios localmente.
    - Reto 2 (Clasificación):
        * 500, 502, 503, 504 -> Son fallos de servidor (cuentan para abrir el circuito).
        * 400, 401, 403, 404 -> Fallos del cliente (NO cuentan, son ignorados por el CB).
        * Timeout de red -> Fallo de servidor (cuenta para abrir el circuito).
    """

    ESTADO_CERRADO = "CERRADO"
    ESTADO_ABIERTO = "ABIERTO"
    ESTADO_SEMIABIERTO = "SEMIABIERTO"

    def __init__(self, umbral_fallos=3, timeout_reset=10):
        self.umbral_fallos = umbral_fallos
        self.timeout_reset = timeout_reset
        self.estado = self.ESTADO_CERRADO
        self._fallos_consecutivos = 0
        self._ultima_falla = 0

    def _es_fallo_servidor(self, error, status_code=None):
        if status_code and status_code >= 500:
            return True
        if isinstance(error, TimeoutError) or "Timeout" in str(error):
            return True
        return False

    def check_estado(self):
        """Revisa si el circuito está abierto y, si pasó el timeout, lo pasa a semiabierto."""
        if self.estado == self.ESTADO_ABIERTO:
            if time.time() - self._ultima_falla >= self.timeout_reset:
                logging.info("Timeout completado. Pasando circuito a estado SEMIABIERTO.")
                self.estado = self.ESTADO_SEMIABIERTO
            else:
                raise Exception("Circuit Breaker ABIERTO - Petición rechazada inmediatamente.")

    def registrar_exito(self):
        if self.estado == self.ESTADO_SEMIABIERTO:
            logging.info("Éxito en SEMIABIERTO. Restaurando circuito a CERRADO.")
            self.estado = self.ESTADO_CERRADO
        self._fallos_consecutivos = 0

    def registrar_falla(self, error, status_code=None):
        if not self._es_fallo_servidor(error, status_code):
            return # Ignoramos errores de cliente (ej. 401)
            
        self._fallos_consecutivos += 1
        self._ultima_falla = time.time()

        if self.estado == self.ESTADO_SEMIABIERTO or self._fallos_consecutivos >= self.umbral_fallos:
            logging.error(f"¡Demasiados fallos ({self._fallos_consecutivos})! Abriendo circuito.")
            self.estado = self.ESTADO_ABIERTO

    def call(self, func, *args, **kwargs):
        """Ejecuta una función protegiéndola con el Circuit Breaker."""
        self.check_estado()
        
        try:
            resultado = func(*args, **kwargs)
            # Para simulación, asumimos que si no hay excepción fue un éxito a nivel de red
            # En un caso real HTTP, validaríamos el status_code del response también.
            self.registrar_exito()
            return resultado
        except Exception as e:
            # En un caso real HTTP, extraeríamos el status_code si aplica
            self.registrar_falla(e)
            raise e
