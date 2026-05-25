import asyncio
import time
import base64
import json
import logging
from token_manager import TokenManager, HttpClientBase

logging.basicConfig(level=logging.INFO, format='\n%(message)s')

def generar_mock_token(segundos_validez):
    exp_time = int(time.time()) + segundos_validez
    mock_payload = base64.b64encode(json.dumps({"sub": "user_demo", "exp": exp_time}).encode()).decode().rstrip('=')
    return f"header.{mock_payload}.signature"

def ui_logout_listener(evento):
    logging.warning(f"-> [UI COMPONENT] Recibió evento de desconexión: {evento}. Mostrando modal de 'Sesión Caducada'.")

async def main():
    print("==========================================")
    print("SIMULADOR JWT - 5 ESCENARIOS DE VALIDACION")
    print("==========================================\n")

    tm = TokenManager()
    tm.add_observer(ui_logout_listener)
    client = HttpClientBase(tm)

    print("--- ESCENARIO 1: Login Exitoso ---")
    token_valido = generar_mock_token(3600) # Expira en 1 hora
    tm.store_tokens(token_valido, "refresh_token_123")
    print(f"Estado de login: {tm.is_logged_in}")

    print("\n--- ESCENARIO 2: Acceso con token válido ---")
    res, status = await client.fetch("/api/perfil")
    print(f"Respuesta HTTP {status}: {res}")

    print("\n--- ESCENARIO 3: Expiración Inminente (Refresh Proactivo) ---")
    # Generamos un token que expira en 10 segundos.
    # El is_expiring_soon() tiene buffer de 60s, por lo que detectará que expira pronto.
    token_casi_expirado = generar_mock_token(10)
    tm.store_tokens(token_casi_expirado, "refresh_token_123")
    # Al hacer la llamada, el cliente hará refresh proactivo ANTES de enviar.
    res, status = await client.fetch("/api/datos")
    print(f"Respuesta HTTP {status}: {res}")

    print("\n--- ESCENARIO 4: Expiración Inesperada 401 (Refresh Reactivo) ---")
    # Supongamos que el servidor decide revocar nuestro token actual (ej. lo borraron de la DB)
    # y nos responde con 401 a pesar de que localmente parece válido.
    res, status = await client.fetch("/api/pagos", simular_error="401")
    print(f"Respuesta HTTP {status}: {res}")

    print("\n--- ESCENARIO 5: Expiración del Refresh Token (Logout) ---")
    # Almacenamos un access_token expirado para forzar refresh proactivo
    token_expirado = generar_mock_token(-100) 
    # Y asignamos un refresh token que sabemos que el mock del server rechazará
    tm.store_tokens(token_expirado, "expired_refresh_token")
    
    res, status = await client.fetch("/api/dashboard")
    print(f"Respuesta HTTP {status}: {res}")
    print(f"Estado de login final: {tm.is_logged_in}")

if __name__ == "__main__":
    asyncio.run(main())
