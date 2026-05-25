"""
DECISIONES DE DISEÑO — Monitor de Inventario EcoMarket
=======================================================
INTERVALO_BASE = 5s
  → Trade-off: Al ser un dashboard de inventario, 5s ofrece un buen balance
    entre frescura de datos y carga del servidor. Un intervalo más corto
    generaría excesivas peticiones vacías si los datos no cambian a cada segundo.

INTERVALO_MAX = 60s
  → Trade-off: El cliente descansa más reduciendo carga en la red en períodos 
    de nula actividad, pero los datos pueden tener hasta 60s de retraso.
    Para EcoMarket esto es aceptable porque el stock global no es transaccional 
    en tiempo real para lectura (a menos que se use WebSocket).

TIMEOUT = 10s
  → Si el servidor no responde en 10s, el cliente lo trata como fallo 
    y aplica backoff. Sin timeout, el ciclo quedaría bloqueado esperando 
    eternamente una respuesta, rompiendo la arquitectura adaptativa.
"""

import asyncio
import aiohttp
import logging

# Configuración básica de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Observable:
    """Clase base para implementar el patrón Observer"""
    def __init__(self):
        # Diccionario: cada clave es un evento, valor es lista de callbacks
        self._observadores = {}

    def suscribir(self, evento, callback):
        if evento not in self._observadores:
            self._observadores[evento] = []
        self._observadores[evento].append(callback)

    def desuscribir(self, evento, callback):
        if evento in self._observadores:
            if callback in self._observadores[evento]:
                self._observadores[evento].remove(callback)

    def notificar(self, evento, datos):
        if evento in self._observadores:
            for cb in self._observadores[evento]:
                try:
                    cb(datos)
                except Exception as e:
                    # Un callback roto NO detiene a los demás
                    logging.error(f"Error en observador para evento '{evento}': {e}")


class ServicioPolling(Observable):
    def __init__(self, url_base, intervalo_base=5):
        super().__init__()
        self.url_base = url_base
        self.intervalo_base = intervalo_base
        self.intervalo_actual = intervalo_base
        self.intervalo_max = 60
        self.ultimo_etag = None
        self._activo = False
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def iniciar(self):
        self._activo = True
        logging.info("Servicio de Polling iniciado.")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            while self._activo:
                await self._consultar(session)
                
                # Respetar el ciclo de inactividad
                if self._activo:
                    await asyncio.sleep(self.intervalo_actual)

    async def _consultar(self, session):
        headers = {}
        if self.ultimo_etag:
            headers['If-None-Match'] = self.ultimo_etag

        try:
            async with session.get(self.url_base, headers=headers) as response:
                status = response.status

                if status == 200:
                    self.ultimo_etag = response.headers.get("ETag", self.ultimo_etag)
                    datos = await response.json()
                    
                    self.notificar("datos_actualizados", datos)
                    self.intervalo_actual = self.intervalo_base # Resetear intervalo
                    
                elif status == 304:
                    self.intervalo_actual = min(self.intervalo_actual * 1.5, self.intervalo_max)
                    logging.info(f"[304] Sin cambios. Nuevo intervalo: {self.intervalo_actual:.1f}s")
                    
                elif status >= 500:
                    self.notificar("error_servidor", f"Error {status}")
                    self.intervalo_actual = min(self.intervalo_actual * 2, self.intervalo_max)
                    logging.warning(f"[5XX] Fallo del servidor. Nuevo intervalo: {self.intervalo_actual:.1f}s")
                    
                else:
                    self.notificar("error_servidor", f"Status inesperado: {status}")

        except asyncio.TimeoutError:
            self.notificar("error_servidor", "Timeout alcanzado")
            self.intervalo_actual = min(self.intervalo_actual * 2, self.intervalo_max)
            logging.warning(f"[Timeout] Servidor no responde. Nuevo intervalo: {self.intervalo_actual:.1f}s")
            
        except aiohttp.ContentTypeError:
            self.notificar("error_servidor", "Formato de respuesta incorrecto (no es JSON)")
        except Exception as e:
            self.notificar("error_servidor", str(e))

    def detener(self):
        self._activo = False
        logging.info("Deteniendo Servicio de Polling...")


# --- OBSERVADORES INDEPENDIENTES ---

def actualizar_ui(datos):
    if not isinstance(datos, list):
        logging.error("Formato de datos no válido, se esperaba una lista de productos.")
        return
        
    logging.info(f"[UI] Datos actualizados. Total elementos: {len(datos)}")

def verificar_stock(datos):
    if not isinstance(datos, list):
        return
    for producto in datos:
        # Simulamos que algunos items pueden tener stock 0 (json placeholder no tiene stock)
        if producto.get("stock", -1) == 0:
            logging.warning(f"[ALERTA] El producto {producto.get('nombre', 'Desconocido')} está AGOTADO!")

def registrar_error(error_msg):
    logging.error(f"[MONITOR ERROR] {error_msg}")


# --- DEMOSTRACIÓN (INTEGRACIÓN ECOMARKET) ---
async def main():
    # Endpoint de prueba genérico
    url = "https://jsonplaceholder.typicode.com/posts"
    monitor = ServicioPolling(url, intervalo_base=2)  # Usamos 2 seg para pruebas rápidas
    
    # 1. Suscribir observadores
    monitor.suscribir("datos_actualizados", actualizar_ui)
    monitor.suscribir("datos_actualizados", verificar_stock)
    monitor.suscribir("error_servidor", registrar_error)
    
    # 2. Iniciar polling
    tarea_polling = asyncio.create_task(monitor.iniciar())
    
    # 3. Dejamos que haga polling por unos ciclos
    await asyncio.sleep(10)
    
    # 4. Detener limpiamente
    monitor.detener()
    await tarea_polling

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
