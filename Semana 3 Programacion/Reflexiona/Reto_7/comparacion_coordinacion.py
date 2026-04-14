import asyncio
import time

# ==========================================
# Entorno de Prueba y Mock de Peticiones
# ==========================================
async def mock_endpoint(nombre, delay, exc=None):
    """Simula una petición ruteada a un endpoint HTTP con latencia."""
    try:
        await asyncio.sleep(delay)
        if exc:
            raise exc
        return f"Datos_de_{nombre}"
    except asyncio.CancelledError:
        # Capturamos la cancelación si otra petición estalló en FIRST_EXCEPTION
        raise

def crear_escenario():
    """
    Escenario base dictado en las instrucciones:
    productos=200ms, categorías=100ms, perfil=500ms, notificaciones=TIMEOUT
    """
    return [
        asyncio.create_task(mock_endpoint("productos", 0.200), name="productos"),
        asyncio.create_task(mock_endpoint("categorias", 0.100), name="categorias"),
        asyncio.create_task(mock_endpoint("perfil", 0.500), name="perfil"),
        # Simulamos que timeout o falla estricta ocurre a los 2.0s por practicidad en testing
        asyncio.create_task(mock_endpoint("notificaciones", 2.000, asyncio.TimeoutError("Timeout Error!")), name="notificaciones")
    ]

# ==========================================
# Estrategia 1: asyncio.gather()
# ==========================================
async def est_1_gather():
    print("\n--- 1. Estrategia: asyncio.gather() ---")
    tareas = crear_escenario()
    start = time.time()
    
    try:
        # Por defecto sin return_exceptions=True, una falla propaga a todo
        resultados = await asyncio.gather(*tareas)
        print(f"Resultados finales: {resultados}")
    except Exception as e:
        print(f"❌ ¡Abortado por Excepción en 'gather'! Error: {e}")
        print(f"⏱️ Tiempos: Pese a que 'categorías' terminó en 100ms, el usuario vió pantalla en blanco por {time.time()-start:.3f}s y de la nada CRASHEÓ todo por culpa de las Notificaciones tardías.")


# ==========================================
# Estrategia 2: asyncio.wait(FIRST_COMPLETED)
# ==========================================
async def est_2_wait_first_completed():
    print("\n--- 2. Estrategia: asyncio.wait(FIRST_COMPLETED) ---")
    pendientes = set(crear_escenario())
    start = time.time()
    primer_dato = False
    
    while pendientes:
        hechas, pendientes = await asyncio.wait(pendientes, return_when=asyncio.FIRST_COMPLETED)
        for t in hechas:
            if not primer_dato:
                primer_dato = True
                print(f"⏱️ UX SUPERIOR: ¡Primer dato renderizado en pantalla en apenas {time.time()-start:.3f}s!")
            
            try:
                res = t.result()
                print(f"✅ Mostrando en UI: {res} (En tiempo: {time.time()-start:.3f}s)")
            except Exception as e:
                print(f"⚠️ Error marginal interceptado en {t.get_name()}: {e} (Mostrando UI de 'Campanita Desconectada' pero la app es utilizable)")


# ==========================================
# Estrategia 3: asyncio.as_completed()
# ==========================================
async def est_3_as_completed():
    print("\n--- 3. Estrategia: asyncio.as_completed() ---")
    tareas = crear_escenario()
    start = time.time()
    primer_dato = False
    
    for futuro in asyncio.as_completed(tareas):
        try:
            res = await futuro
            if not primer_dato:
                primer_dato = True
                print(f"⏱️ UX SUPERIOR: ¡Primer dato en {time.time()-start:.3f}s!")
            print(f"✅ Desplegando a medida: {res} ({time.time()-start:.3f}s)")
        except Exception as e:
            print(f"⚠️ Falla asíncrona tolerada: {e} en loop temporal a los {time.time()-start:.3f}s")


# ==========================================
# Estrategia 4: asyncio.wait(FIRST_EXCEPTION)
# ==========================================
async def est_4_wait_first_exception():
    print("\n--- 4. Estrategia: asyncio.wait(FIRST_EXCEPTION) ---")
    pendientes = set(crear_escenario())
    start = time.time()
    
    # Ésta pausará hasta que a) se hagan todas y no haya fallos, o b) al primer error
    hechas, pendientes = await asyncio.wait(pendientes, return_when=asyncio.FIRST_EXCEPTION)
    
    print(f"⏱️ Interrupción detectada en {time.time()-start:.3f}s. Inspeccionando lote:")
    HuboExcepcion = False
    for t in hechas:
        try:
            res = t.result()
            print(f"Terminadas limpias antes del quiebre: {t.get_name()}")
        except Exception as e:
            HuboExcepcion = True
            print(f"🔥 Excepción Fatal que destruyó el proceso: Error en {t.get_name()} -> {e}")
            
    if HuboExcepcion:
        print("🚫 Anulando/Cancelando explícitamente el resto de las tareas segundarias que volaban en vano...")
        for p in pendientes:
            p.cancel()

async def run_escenarios():
    await est_1_gather()
    await asyncio.sleep(0.5)
    await est_2_wait_first_completed()
    await asyncio.sleep(0.5)
    await est_3_as_completed()
    await asyncio.sleep(0.5)
    await est_4_wait_first_exception()

if __name__ == "__main__":
    asyncio.run(run_escenarios())
