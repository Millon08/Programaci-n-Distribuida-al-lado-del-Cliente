import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from abc import ABC, abstractmethod

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
BASE_URL        = "http://ecomarket.local/api/v1"
TOKEN           = "eyJ0eXAiO..."          # token proporcionado en el examen
INTERVALO_BASE  = 5                       # segundos entre consultas
INTERVALO_MAX   = 60                      # máximo de backoff
TIMEOUT         = 10                      # segundos de timeout por petición

# ─── INTERFAZ OBSERVADOR ──────────────────────────────────────────────────────
class Observador(ABC):
    @abstractmethod
    async def actualizar(self, inventario: dict):
        pass

# ─── OBSERVABLE ───────────────────────────────────────────────────────────────
class MonitorInventario:
    def __init__(self):
        self._observadores = []
        self._ultimo_etag = None
        self._ultimo_estado = None
        self._ejecutando = False
        self._intervalo = INTERVALO_BASE

    def suscribir(self, obs: Observador):
        if obs not in self._observadores:
            self._observadores.append(obs)

    def desuscribir(self, obs: Observador):
        if obs in self._observadores:
            self._observadores.remove(obs)

    async def _notificar(self, inventario: dict):
        for obs in self._observadores:
            try:
                # Se llama a actualizar en todos los observadores de forma idéntica
                # sin condicionales de tipo
                await obs.actualizar(inventario)
            except Exception as e:
                # Evitamos que un observador con problemas interrumpa la notificación a los demás
                logger.error(f"Error al notificar al observador {obs.__class__.__name__}: {e}")

    async def _consultar_inventario(self, session: aiohttp.ClientSession):
        """
        Consulta la API y maneja los distintos códigos HTTP diferenciando
        la respuesta correcta, la falta de cambios, y los errores.
        Retorna la tupla (estado, datos) para que el ciclo de polling tome acciones.
        Nunca propaga excepciones al ciclo.
        """
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json"
        }
        if self._ultimo_etag:
            headers["If-None-Match"] = self._ultimo_etag

        try:
            async with session.get(f"{BASE_URL}/inventario", headers=headers, timeout=TIMEOUT) as response:
                status = response.status

                if status == 200:
                    datos = await response.json()
                    
                    # Validación del body de la respuesta
                    if not isinstance(datos, dict) or "productos" not in datos or datos["productos"] is None:
                        logger.error("JSON recibido inválido o sin el campo 'productos'")
                        return ("invalid_json", None)

                    etag = response.headers.get("ETag")
                    if etag:
                        self._ultimo_etag = etag
                        
                    return ("200", datos)

                elif status == 304:
                    logger.debug("304 Not Modified - El inventario no cambió")
                    return ("304", None)

                elif 400 <= status <= 499:
                    # 400 o 401 registran el error y no reintentan inmediatamente (el ciclo pasa y vuelve al intervalo normal)
                    logger.error(f"Error HTTP {status}: Petición inválida o no autorizada.")
                    return ("4xx", None)

                elif status >= 500:
                    logger.warning(f"Error HTTP {status}: Servidor con problemas.")
                    return ("5xx", None)

                else:
                    logger.warning(f"HTTP Status no manejado: {status}")
                    return ("other", None)

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            # Capturamos Timeout y ConnectionError; no propagamos al ciclo
            logger.warning(f"Error de red o timeout ({type(e).__name__}). Se reintentará en el próximo ciclo.")
            return ("net_error", None)
        except Exception as e:
            logger.error(f"Error inesperado al consultar inventario: {e}")
            return ("net_error", None)

    async def iniciar(self):
        """
        Inicia el ciclo de polling asíncrono con backoff adaptativo.
        """
        self._ejecutando = True
        logger.info("Iniciando monitor de inventario...")

        async with aiohttp.ClientSession() as session:
            while self._ejecutando:
                tipo, datos = await self._consultar_inventario(session)

                if tipo == "200" and datos is not None:
                    # Hubo datos nuevos, se reajusta el intervalo
                    self._intervalo = INTERVALO_BASE
                    
                    # Verificamos si realmente los datos cambiaron
                    if self._ultimo_estado != datos:
                        self._ultimo_estado = datos
                        await self._notificar(datos)
                
                elif tipo == "304":
                    # Mantiene el backoff adaptativo (si 304 acumulados, incrementa despacio)
                    self._intervalo = min(self._intervalo * 1.5, INTERVALO_MAX)

                elif tipo == "5xx":
                    # Backoff marcado para sobrecarga del servidor
                    self._intervalo = min(self._intervalo * 2.0, INTERVALO_MAX)

                # Para tipos 4xx, invalid_json, o net_error, el ciclo simplemente continúa
                # usando el intervalo actual o el que sea necesario sin detenerse, ni resetear ni multiplicar.

                logger.debug(f"Esperando {self._intervalo} segundos...")
                # await no bloqueante
                await asyncio.sleep(self._intervalo)

    def detener(self):
        """
        Solo cambia la bandera de control para un cierre suave,
        sin interrumpir de forma forzada la corrutina principal.
        """
        logger.info("Deteniendo monitor de inventario de forma segura...")
        self._ejecutando = False


# ─── OBSERVADORES CONCRETOS ───────────────────────────────────────────────────
class ModuloCompras(Observador):
    async def actualizar(self, inventario: dict):
        productos_bajos = [p for p in inventario.get("productos", []) if p.get("status") == "BAJO_MINIMO"]
        if productos_bajos:
            print("\n----- 🛒 [COMPRAS] ALERTA DE STOCK -----")
            for p in productos_bajos:
                print(f"🔹 {p.get('nombre')} (ID: {p.get('id')})")
                print(f"    Stock Actual: {p.get('stock')} | Mínimo Permitido: {p.get('stock_minimo')}")
            print("----------------------------------------\n")

class ModuloAlertas(Observador):
    async def actualizar(self, inventario: dict):
        productos_bajos = [p for p in inventario.get("productos", []) if p.get("status") == "BAJO_MINIMO"]
        if not productos_bajos:
            return

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            }

            for p in productos_bajos:
                body = {
                    "producto_id": str(p.get("id")),
                    "stock_actual": int(p.get("stock", 0)),
                    "stock_minimo": int(p.get("stock_minimo", 0)),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                try:
                    async with session.post(f"{BASE_URL}/alertas", headers=headers, json=body, timeout=TIMEOUT) as response:
                        if response.status == 201:
                            logger.info(f"✅ [ALERTAS] Alerta registrada: {body['producto_id']}")
                        elif response.status == 422:
                            logger.error(f"❌ [ALERTAS] Error 422: Datos inválidos al notificar alerta de {body['producto_id']}.")
                        else:
                            logger.warning(f"⚠️ [ALERTAS] Estado HTTP no manejado ({response.status}) para {body['producto_id']}.")
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    logger.warning(f"🌐 [ALERTAS] Error de red enviando alerta {body['producto_id']}: {e}.")
                except Exception as e:
                    logger.error(f"🚨 [ALERTAS] Error inesperado enviando alerta: {e}")

# ─── PUNTO DE ENTRADA ─────────────────────────────────────────────────────────
async def main():
    monitor = MonitorInventario()
    monitor.suscribir(ModuloCompras())
    monitor.suscribir(ModuloAlertas())

    # Se ejecuta de forma asíncrona dentro del Event Loop
    tarea = asyncio.create_task(monitor.iniciar())

    # Simulación temporal (Por ejemplo 30s y luego se apaga ordenadamente)
    await asyncio.sleep(30)
    monitor.detener()
    await tarea

if __name__ == "__main__":
    # Asegura compatibilidad de Event Loop en Windows
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Ejecución terminada manualmente.")
