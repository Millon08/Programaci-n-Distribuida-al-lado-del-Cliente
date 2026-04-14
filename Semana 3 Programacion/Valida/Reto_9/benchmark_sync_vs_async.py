import asyncio
import time
import statistics
import tracemalloc

# ==============================================================
# MOCKS DE RED Y LATENCIA (Sin requests/aiohttp reales para evitar ruido de red externa, probamos arquitectura pura)
# ==============================================================
async def mock_async_req(delay):
    await asyncio.sleep(delay)
    return True

def mock_sync_req(delay):
    time.sleep(delay)
    return True

# ==============================================================
# ESCENARIOS DE PRUEBA
# ==============================================================
def escenario_sync_dashboard(delay):
    for _ in range(4): mock_sync_req(delay)

def escenario_sync_masiva(delay):
    for _ in range(20): mock_sync_req(delay)

def escenario_sync_mixto(delay):
    for _ in range(18): mock_sync_req(delay) # 10 GET, 5 POST, 3 PATCH

async def escenario_async_dashboard(delay):
    await asyncio.gather(*(mock_async_req(delay) for _ in range(4)))

async def escenario_async_masiva(delay):
    await asyncio.gather(*(mock_async_req(delay) for _ in range(20)))

async def escenario_async_mixto(delay):
    await asyncio.gather(*(mock_async_req(delay) for _ in range(18)))

# ==============================================================
# MOTOR DEL BENCHMARK
# ==============================================================
def track_sync(func, delay, num_reqs, iteraciones=10):
    tracemalloc.start()
    tiempos = []
    for _ in range(iteraciones):
        start = time.perf_counter()
        func(delay)
        tiempos.append(time.perf_counter() - start)
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    avg_t = statistics.mean(tiempos)
    return avg_t, peak_mem / 1024.0, num_reqs / avg_t

async def track_async(func_coro, delay, num_reqs, iteraciones=10):
    tracemalloc.start()
    tiempos = []
    for _ in range(iteraciones):
        start = time.perf_counter()
        await func_coro(delay)
        tiempos.append(time.perf_counter() - start)
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    avg_t = statistics.mean(tiempos)
    return avg_t, peak_mem / 1024.0, num_reqs / avg_t

def run_benchmarks():
    latencias = [0.0, 0.1, 0.5] # 0ms, 100ms, 500ms
    escenarios = [
        ("Dashboard (4 rq)", escenario_sync_dashboard, escenario_async_dashboard, 4),
        ("Masiva (20 rq)", escenario_sync_masiva, escenario_async_masiva, 20),
        ("Mixto (18 rq)", escenario_sync_mixto, escenario_async_mixto, 18)
    ]
    
    print("="*90)
    print(f"{'Escenario':<20} | {'Latencia':<8} | {'SYNC Tiempo':<12} | {'ASYNC Tiempo':<12} | {'SPEEDUP':<8}")
    print("="*90)

    for nombre, fn_s, fn_a, reqs in escenarios:
        for lat in latencias:
            t_sync, mem_sync, tp_sync = track_sync(fn_s, lat, reqs)
            t_async, mem_async, tp_async = asyncio.run(track_async(fn_a, lat, reqs))
            
            speedup = t_sync / t_async if t_async > 0.0001 else 0
            
            lat_str = f"{int(lat*1000)}ms"
            print(f"{nombre:<20} | {lat_str:<8} | {t_sync:>8.3f}s   | {t_async:>8.3f}s   | 🚀 {speedup:.1f}x")
    
    print("="*90)
    print("\nBenchmark completado (ver consola o exportar métricas).")

if __name__ == "__main__":
    run_benchmarks()
