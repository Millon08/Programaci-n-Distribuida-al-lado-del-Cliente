import time
import random
import functools
import requests

# Configuración por defecto
MAX_RETRIES = 3
BASE_DELAY = 1  # Segundos

def with_retry(func):
    """
    Decorador que reintenta la función si ocurren errores de red o 5xx.
    Usa Exponential Backoff + Jitter.
    NO reintenta en errores 4xx (excepto 408 o 429 si quisiéramos ser muy estrictos, 
    pero por ahora asumimos 4xx = error del cliente).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        
        while True:
            try:
                # Intentamos ejecutar la función original
                return func(*args, **kwargs)
                
            except requests.exceptions.RequestException as e:
                # Analizamos el error
                es_error_cliente = False
                status_code = None

                if e.response is not None:
                    status_code = e.response.status_code
                    # Si es 4xx (ej: 404, 400), NO reintentamos. Es culpa nuestra.
                    if 400 <= status_code < 500:
                        es_error_cliente = True

                # Si es error del cliente o ya gastamos los intentos, fallamos oficialmente
                if es_error_cliente or retries >= MAX_RETRIES:
                    print(f"❌ Fallo definitivo en {func.__name__} | Status: {status_code} | Error: {e}")
                    raise e

                # Si llegamos aquí, es un error transitorio (5xx o red). A reintentar.
                retries += 1
                
                # FÓRMULA DE EXPONENTIAL BACKOFF: 2^retries
                delay = BASE_DELAY * (2 ** (retries - 1))
                
                # AGREGAMOS JITTER (Variación aleatoria)
                # Esto evita que todos los clientes reintenten EXACTAMENTE al mismo tiempo
                jitter = random.uniform(0, 1)
                final_wait = delay + jitter
                
                print(f"⚠️ Error transitorio ({e}). Reintentando {func.__name__} en {final_wait:.2f}s... (Intento {retries}/{MAX_RETRIES})")
                time.sleep(final_wait)
                
    return wrapper

# ==========================================
# ZONA DE PRUEBAS (TESTS INTERNOS)
# ==========================================
if __name__ == "__main__":
    print("--- 🧪 INICIANDO PRUEBAS DE RESILIENCIA ---")

    # Simulamos un servidor que falla 2 veces y a la 3ra funciona
    intentos_mock = 0
    
    @with_retry
    def funcion_inestable():
        global intentos_mock
        intentos_mock += 1
        if intentos_mock < 3:
            # Simulamos error 503 Service Unavailable
            raise requests.exceptions.HTTPError("Servidor ocupado", response=requests.Response())
        print("✅ ¡Éxito! El servidor respondió.")
        return "Datos recibidos"

    # Inyectamos el código de estado 503 al mock del response para que la lógica lo detecte
    # (Pequeño hack para simular requests sin hacer peticiones reales)
    def simular_fallo_503():
        resp = requests.Response()
        resp.status_code = 503
        raise requests.exceptions.HTTPError("503 Server Error", response=resp)

    # Redefinimos para usar el simulador más preciso
    intentos_mock = 0
    @with_retry
    def obtener_datos_simulados():
        global intentos_mock
        intentos_mock += 1
        if intentos_mock < 3:
            simular_fallo_503()
        print("✅ Conexión exitosa al tercer intento.")
        return "OK"

    try:
        obtener_datos_simulados()
        print("\n🏆 PRUEBA PASADA: El sistema se recuperó automáticamente.")
    except Exception as e:
        print(f"\n❌ PRUEBA FALLIDA: {e}")