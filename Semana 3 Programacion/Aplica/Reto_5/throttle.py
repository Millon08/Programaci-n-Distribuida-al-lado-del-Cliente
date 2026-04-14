import asyncio
import aiohttp
import time

# --- Mocking Básico ---
# Este entorno de simulación emula fallos de red, latencia o estatus de respuesta 
class MockResponse:
    def __init__(self, status, data):
        self.status = status
        self._data = data
    
    async def json(self):
        return self._data

class MockSession:
    async def get(self, url, delay=0.5, status=200):
        # Simulamos la demora natural de la red
        await asyncio.sleep(delay)
        if status == 401:
            raise aiohttp.ClientResponseError(None, None, message="Unauthorized", status=status)
        return MockResponse(status, {"data": f"response from {url}"})


# --- 1. Timeout Individual por Petición ---
async def fetch_con_timeout(session, nombre, url, delay, timeout_segundos):
    print(f"[{time.time():.2f}] Iniciando '{nombre}' (Timeout config: {timeout_segundos}s)")
    
    async def request_real():
        response = await session.get(url, delay=delay)
        return await response.json()
        
    try:
        # Aquí envolvemos específicamente con asyncio.wait_for cada corrutina
        resultado = await asyncio.wait_for(request_real(), timeout=timeout_segundos)
        print(f"[{time.time():.2f}] ✅ Completado '{nombre}'")
        return nombre, resultado
    except asyncio.TimeoutError:
        print(f"[{time.time():.2f}] ❌ Timeout en '{nombre}'. Excedió los {timeout_segundos}s")
        return nombre, Exception("Timeout")


# --- 2. Cancelación de Tareas en Grupo ---
def cancel_remaining(tareas):
    for tarea in tareas:
        if not tarea.done():
            tarea.cancel()
            print(f"🚫 Tarea '{tarea.get_name()}' cancelada preventivamente.")

async def cargar_con_cancelacion(session):
    print("\n--- Ejecutando Escenario 2: Cancelación si Perfil da error 401 ---")
    
    async def request_normal(nombre, delay):
        try:
            await session.get("mock_url", delay=delay)
            print(f"✅ {nombre} terminó satisfactoriamente")
        except asyncio.CancelledError:
            print(f"🚫 {nombre} interceptó una cancelación y liberó recursos.")
            raise  # Elevamos la cancelación para que el event loop la devore correctamente
            
    async def request_perfil():
        await session.get("mock_url", delay=0.5, status=401)
        
    tarea_productos = asyncio.create_task(request_normal("Productos", 2.0), name="productos")
    tarea_cats = asyncio.create_task(request_normal("Categorías", 3.0), name="categorias")
    tarea_perfil = asyncio.create_task(request_perfil(), name="perfil")
    
    tareas = [tarea_productos, tarea_cats, tarea_perfil]
    
    while tareas:
        hechas, pendientes = await asyncio.wait(tareas, return_when=asyncio.FIRST_COMPLETED)
        for t in hechas:
            try:
                await t
            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    print("⚠️ Recibido HTTP 401 de Perfil (Acceso Denegado).")
                    cancel_remaining(pendientes)
        
        tareas = list(pendientes)


# --- 3. Cargar con Prioridad Estructurada ---
async def cargar_con_prioridad(session):
    print("\n--- Ejecutando Escenario 3: Cargar con Prioridad Dinámica ---")
    
    async def iteracion_mock(nombre, delay):
        await asyncio.sleep(delay)
        return nombre
        
    t_productos = asyncio.create_task(iteracion_mock("productos", 0.5), name="productos")
    t_perfil = asyncio.create_task(iteracion_mock("perfil", 0.6), name="perfil")
    t_categorias = asyncio.create_task(iteracion_mock("categorias", 2.0), name="categorias")
    t_notif = asyncio.create_task(iteracion_mock("notificaciones", 3.0), name="notificaciones")
    
    pendientes = {t_productos, t_perfil, t_categorias, t_notif}
    
    # Marcamos las peticiones core para lanzar un pre-render o accion.
    criticas = {"productos", "perfil"}
    completadas_criticas = set()
    ya_renderizado = False
    
    while pendientes:
        hechas, pendientes = await asyncio.wait(pendientes, return_when=asyncio.FIRST_COMPLETED)
        
        for t in hechas:
            nombre = t.get_name()
            print(f"📥 Recibí la carga de: '{nombre}'")
            if nombre in criticas:
                completadas_criticas.add(nombre)
                
        if completadas_criticas == criticas and not ya_renderizado:
            print("-" * 50)
            print("🚀 ¡Las tareas críticas han llegado! Renderizando Dashboard Parcial al usurio de forma inmediata...")
            print("-" * 50)
            ya_renderizado = True

# --- Rutina Principal ---
async def test_estrategias():
    session = MockSession()
    
    print("\n--- Ejecutando Escenario 1: Timeouts Individuales ---")
    # Según Instrucciones:
    # /categorias tardara 8s, pero su max timeout será solo 3s.
    t1 = fetch_con_timeout(session, "productos", "mock_url", delay=1.0, timeout_segundos=5.0)
    t2 = fetch_con_timeout(session, "categorias", "mock_url", delay=8.0, timeout_segundos=3.0)
    t3 = fetch_con_timeout(session, "perfil", "mock_url", delay=1.5, timeout_segundos=2.0)
    
    # Await group. Productos y perfil llegan a tiempo, categorias hace throw exception en su wrapper que no arruina las demas
    await asyncio.gather(t1, t2, t3)
    
    await cargar_con_cancelacion(session)
    
    await cargar_con_prioridad(session)
    
    print("\n✅ Todas las pruebas asíncronas han terminado.\n")


if __name__ == "__main__":
    asyncio.run(test_estrategias())
