import aiohttp
import asyncio
import time
from aiohttp import web

# ==========================================
# 1. Implementación de SmartSession
# ==========================================
class SmartSession:
    """
    Drop-in replacement para aiohttp.ClientSession que inyecta parámetros
    optimizados de red y provee monitoreo del TCP Pool en tiempo real.
    """
    def __init__(self, limit=100, keepalive_timeout=30.0, **kwargs):
        # El TCPConnector es el orquestador real de sockets
        # limit=0 significa "Infinito" (Peligroso)
        self.limit = limit
        self._connector = aiohttp.TCPConnector(
            limit=limit, 
            keepalive_timeout=keepalive_timeout,
            enable_cleanup_closed=True # Recomendado para evitar leaks
        )
        self._session = aiohttp.ClientSession(connector=self._connector, **kwargs)
        
    async def __aenter__(self):
        await self._session.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        await self._session.__aexit__(exc_type, exc, tb)
        
    def get(self, *args, **kwargs):
        """Redirigimos los handlers CRUD directo a la sesión subyacente"""
        return self._session.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self._session.post(*args, **kwargs)
        
    def _obtener_metricas_internas(self):
        # Inspección "por debajo de la mesa" al TCP Connector
        # _acquired son conexiones asignadas a una tarea actualmente en curso
        adquiridas = sum(len(c) for c in self._connector._acquired.values())
        # _conns son las conexiones TCP abiertas mantenidas activas (keep-alive) pero de momento desocupadas
        reutilizables = sum(len(c) for c in self._connector._conns.values())
        return adquiridas, reutilizables

    def log_health_check(self):
        adq, disp = self._obtener_metricas_internas()
        lim_str = "Ilimitado" if self.limit == 0 else str(self.limit)
        print(f"🏊 [HealthCheck] Pool límite: {lim_str} | Abiertas ocupadas (En Vuelo): {adq} | Abiertas Disponibles (Keep-Alive): {disp}")
        
    async def monitor_continuo(self, intervalo=0.04):
        """Tarea background que escupe latidos para observar como viaja el buffer TCP."""
        try:
            while not self._session.closed:
                self.log_health_check()
                await asyncio.sleep(intervalo)
        except asyncio.CancelledError:
            pass


# ==========================================
# 2. Servidor Mock Real 
# ==========================================
async def handle_test(request):
    # Simula latencia del servidor backend (100ms)
    await asyncio.sleep(0.1)
    return web.json_response({"estado": "OK"})

async def levantar_servidor():
    app = web.Application()
    app.router.add_get('/test', handle_test)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    return runner

# ==========================================
# 3. Benchmark de Conexiones
# ==========================================
async def ejecutar_escenario(limit_val, num_peticiones=50):
    print(f"\n{'-'*60}")
    print(f"🚀 INICIANDO TEST: Configuración Pool = {limit_val if limit_val > 0 else 'ILIMITADO (0)'}")
    print(f"{'-'*60}")
    
    start_time = time.time()
    
    async with SmartSession(limit=limit_val) as session:
        # Iniciar Health Checker
        monitor = asyncio.create_task(session.monitor_continuo(0.04))
        
        async def hacer_peticion():
            # async with cierra la promesa, dictando "devuelve el hilo a disponibles" al acabar
            async with session.get("http://localhost:8080/test") as resp:
                await resp.read()
                
        tareas = [asyncio.create_task(hacer_peticion()) for _ in range(num_peticiones)]
        await asyncio.gather(*tareas)
        
        # Un ultimo healthcheck para ver como queda la sesion post-trabajo
        session.log_health_check()
        monitor.cancel()
        
    lapso = time.time() - start_time
    print(f"\n📊 RESULTADOS (Límite TCP={limit_val}):")
    print(f"   -> Tiempo Total:    {lapso:.3f} s")
    print(f"   -> Throughput:      {num_peticiones/lapso:.1f} req/s")


async def main():
    # Levantamos localmente un minihub TCP real para que Python maneje sockets verídicos
    runner = await levantar_servidor()
    print("API Mock Server en pie en http://localhost:8080/test")
    
    try:
        # Escenario 1: Estrangulado conservador
        await ejecutar_escenario(limit_val=5)
        
        # Escenario 2: Generoso predeterminado
        await ejecutar_escenario(limit_val=20)
        
        # Escenario 3: Peligrosamente Infinito (0)
        await ejecutar_escenario(limit_val=0)
        
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
